# -*- coding: utf-8 -*-

import sqlite3
import typing as t
from os import remove
from time import time

from drui.metrics import Tag


class Database:
    """
    Handles storage and retrieval of container registry metadata.
    """
    def __init__(self, conf, worker: bool = False):
        # TODO: need worker flag for windows ???
        self.conf = conf
        self.path: str = './metrics.db'
        self._init_db()

        # remove the database file if the registry URL has changed
        # TODO: on Windows can`t get remove database`
        endpoint = self.conf.get('endpoint', section='registry')
        if self.get_registry() != endpoint and worker:
            remove(self.path)
            self._init_db()
            self.set_registry(endpoint)

    def _init_db(self) -> None:
        """
        Create database schema with required tables and indexes if they don't exist.

        Tables:
          - registries: stores the current registry endpoint
          - stats: tracks synchronization statistic
          - images: list of image names
          - tags: list of image tags with metadata
          - layers: list of layers
          - tag_layers: junction table linking tags to their constituent layers
        """
        with sqlite3.connect(self.path) as conn:
            conn.executescript('''
                               CREATE TABLE IF NOT EXISTS [registries]
                               (
                                   id       INTEGER PRIMARY KEY DEFAULT 1,
                                   endpoint TEXT
                               );

                               CREATE TABLE IF NOT EXISTS [stats]
                               (
                                   id        INTEGER PRIMARY KEY DEFAULT 1,
                                   timestamp TEXT NOT NULL,
                                   status    TEXT,
                                   message   TEXT
                               );

                               CREATE TABLE IF NOT EXISTS [images]
                               (
                                   id   INTEGER PRIMARY KEY AUTOINCREMENT,
                                   name TEXT NOT NULL,
                                   UNIQUE (name)
                               );

                               CREATE TABLE IF NOT EXISTS [tags]
                               (
                                   id       INTEGER PRIMARY KEY AUTOINCREMENT,
                                   image_id INTEGER  NOT NULL,
                                   digest   INTEGER  NOT NULL,
                                   name     TEXT     NOT NULL,
                                   os       TEXT     NOT NULL,
                                   arch     TEXT     NOT NULL,
                                   created  DATETIME NOT NULL,
                                   FOREIGN KEY (image_id) REFERENCES [images] (id) ON DELETE CASCADE,
                                   UNIQUE (image_id, name)
                               );

                               CREATE TABLE IF NOT EXISTS [layers]
                               (
                                   id     INTEGER PRIMARY KEY AUTOINCREMENT,
                                   digest TEXT   NOT NULL UNIQUE,
                                   size   BIGINT NOT NULL
                               );

                               CREATE TABLE IF NOT EXISTS [tag_layers]
                               (
                                   tag_id      INTEGER NOT NULL,
                                   layer_id    INTEGER NOT NULL,
                                   layer_order INTEGER NOT NULL,
                                   FOREIGN KEY (tag_id) REFERENCES [tags] (id) ON DELETE CASCADE,
                                   FOREIGN KEY (layer_id) REFERENCES [layers] (id),
                                   PRIMARY KEY (tag_id, layer_id)
                               );

                               CREATE INDEX IF NOT EXISTS [idx_tags_image_id] ON [tags] (image_id);
                               CREATE INDEX IF NOT EXISTS [idx_tags_created] ON [tags] (created);
                               CREATE INDEX IF NOT EXISTS [idx_tag_layers_tag_id] ON [tag_layers] (tag_id);
                               CREATE INDEX IF NOT EXISTS [idx_tag_layers_layer_id] ON [tag_layers] (layer_id);
                               CREATE INDEX IF NOT EXISTS [idx_layers_digest] ON [layers] (digest);
                               ''')

    def set_registry(self, endpoint: str) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute('''
                         INSERT OR REPLACE INTO [registries] (id, endpoint)
                         VALUES (1, ?)
                         ''', (endpoint,)
                         )

    def get_registry(self) -> t.Optional[str]:
        result = self.search('''
                             SELECT endpoint
                             FROM [registries]
                             LIMIT 1
                             ''')
        return result[0]['endpoint'] if result else None

    def update_stats(self, status: t.Optional[str] = None, error: t.Optional[str] = None) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute('''
                         INSERT OR REPLACE INTO [stats] (id, timestamp, status, message)
                         VALUES (1, ?, ?, ?)
                         ''', (
                time(),
                status,
                error
            ))

    def save(self, tag: Tag) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            cursor = conn.execute(
                "INSERT OR IGNORE INTO [images] (name) VALUES (?)",
                (tag.image,)
            )
            image_id = cursor.lastrowid if cursor.rowcount else None
            if not image_id:
                cursor = conn.execute(
                    "SELECT id FROM [images] WHERE name = ?",
                    (tag.image,)
                )
                image_id = cursor.fetchone()[0]

            # add tag
            cursor = conn.execute('''
                INSERT OR REPLACE INTO [tags] 
                (image_id, digest, name, os, arch, created) 
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (image_id, tag.digest, tag.tag, tag.os, tag.arch, tag.created))
            tag_id = cursor.lastrowid if cursor.rowcount else None

            # add layers
            for order, layer in enumerate(tag.layers):
                cursor = conn.execute('''
                                      INSERT OR IGNORE INTO [layers] (digest, size)
                                      VALUES (?, ?)
                                      ''', (layer['digest'], layer['size']))

                layer_id = cursor.lastrowid if cursor.rowcount else None
                if not layer_id:
                    cursor = conn.execute(
                        "SELECT id FROM [layers] WHERE digest = ?",
                        (layer['digest'],)
                    )
                    layer_id = cursor.fetchone()[0]

                # create link tag-layer
                conn.execute('''
                    INSERT OR REPLACE INTO [tag_layers] 
                    (tag_id, layer_id, layer_order) 
                    VALUES (?, ?, ?)
                ''', (tag_id, layer_id, order))

    def remove(self, image: str, tag) -> None:
        with sqlite3.connect(self.path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")

            conn.execute("""
                         DELETE
                         FROM tags
                         WHERE name = ?
                           AND image_id = (SELECT id FROM images WHERE name = ?)
                         """,
                         (tag, image))

            conn.execute("""
                         DELETE
                         FROM images
                         WHERE id NOT IN (SELECT image_id FROM tags);
                         """)

            conn.execute("""
                         DELETE
                         FROM layers
                         WHERE id NOT IN (SELECT layer_id FROM tag_layers);
                         """)

    def search(self, sql: str) -> t.List[t.Dict[str, str]]:
        with sqlite3.connect(self.path) as conn:
            cur = conn.cursor()
            cur.execute(sql)

        return [
            dict((cn[0], row[i]) for i, cn in enumerate(cur.description))
            for row in cur.fetchall()
        ]

    def tags(self) -> t.List[t.Dict[str, str]]:
        return self.search("""
                           SELECT image.name AS image, tag.name AS tag
                           FROM [images] image
                                    JOIN [tags] tag ON image.id = tag.image_id
                           ORDER BY image.name, tag.name
                           """)

    def stats(self) -> t.Dict[str, str]:
        result = self.search('''
                             SELECT timestamp, status, message
                             FROM [stats]
                             ORDER BY timestamp DESC
                             LIMIT 1
                             ''')
        return result[0] if result else {}

    def size(self) -> str:
        return self.search('SELECT SUM(size) AS size FROM [layers]')[0]['size']

    def images(self) -> str:
        return self.search('SELECT COUNT(id) AS images FROM [images]')[0]['images']

    def layers(self) -> str:
        return self.search('SELECT COUNT(id) AS layers FROM [layers]')[0]['layers']

    def dublicates(self) -> t.List[t.Dict[str, t.List[str]]]:
        items = self.search('''
                            SELECT tag.digest AS digest, img.name AS image, tag.name AS tag
                            FROM tags tag
                                     JOIN images img ON tag.image_id = img.id
                            WHERE tag.digest IN
                                  (SELECT digest FROM tags GROUP BY digest HAVING COUNT(DISTINCT image_id) > 1)
                            ORDER BY tag.digest, img.id;
                            ''')
        dublicates = {}
        for item in items:
            digest = item['digest']
            dublicates.setdefault(digest, [])
            dublicates[digest].append(f"{item['image']}:{item['tag']}")

        return [{'digest': digest, 'images': images} for digest, images in dublicates.items()]

    def newest(self) -> t.List[t.Dict[str, str]]:
        items = self.search('''
                            SELECT image.name AS image, tag.name AS tag, tag.created AS created
                            FROM [images] image
                                     JOIN [tags] tag ON image.id = tag.image_id
                            ORDER BY tag.created DESC
                            LIMIT 3
                            ''')
        return [{'image': f"{item['image']}:{item['tag']}", 'created': item['created']} for item in items]

    def oldest(self) -> t.List[t.Dict[str, str]]:
        items = self.search('''
                            SELECT image.name AS image, tag.name AS tag, tag.created AS created
                            FROM [images] image
                                     JOIN [tags] tag ON image.id = tag.image_id
                            ORDER BY tag.created
                            LIMIT 3
                            ''')
        return [{'image': f"{item['image']}:{item['tag']}", 'created': item['created']} for item in items]

    def raw(self):
        items = self.search('''
                            WITH last_tags AS (SELECT image_id,
                                                      id   AS tag_id,
                                                      name AS tag,
                                                      created,
                                                      digest,
                                                      ROW_NUMBER() OVER (PARTITION BY image_id ORDER BY created DESC)
                                                           AS rn
                                               FROM tags)
                            SELECT i.name,
                                   COALESCE(tag_count.tags, 0) AS tags,
                                   COALESCE(SUM(l.size), 0)    AS size,
                                   lt.tag                      AS latest,
                                   lt.created
                            FROM images i
                                     LEFT JOIN (SELECT image_id, COUNT(*) AS tags FROM tags GROUP BY image_id) tag_count
                                               ON i.id = tag_count.image_id
                                     LEFT JOIN last_tags lt ON i.id = lt.image_id AND lt.rn = 1
                                     LEFT JOIN tag_layers tl ON lt.tag_id = tl.tag_id
                                     LEFT JOIN layers l ON tl.layer_id = l.id
                            GROUP BY i.id, i.name, lt.created, lt.tag, lt.digest
                            ORDER BY i.name;
                            ''')
        return {item['name']: item for item in items}
