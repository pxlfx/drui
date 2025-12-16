import typing as t

from drui.common.config import ConfigParser
from drui.common.logging import get_logger
from drui.metrics import STATUSES
from drui.metrics import Tag
from drui.metrics.database import Database
from drui.registry import Registry


class ProcessingImageError(Exception):
    def __init__(self, *args):
        super().__init__(*args)


class Metrics:
    """
    Client for collecting registry metrics.
    """

    def __init__(self, conf: ConfigParser) -> None:
        self.conf = conf
        self.db = Database(self.conf)
        self.log = get_logger(__name__)

        endpoint = self.conf.get('endpoint', section='registry')
        username = self.conf.get('username', section='metrics')
        password = self.conf.get('password', section='metrics')
        self.registry = Registry(endpoint, username=username, password=password)

    def run(self):
        self.db.update_stats(status=STATUSES.in_progress)

        try:
            tags = []
            db_tags = [f'{item["image"]}:{item["tag"]}' for item in self.db.tags()]
            catalog = self._catalog()

            for image in catalog:
                for tag in self._tags(image):
                    tag_name = f'{image}:{tag}'
                    tags.append(tag_name)
                    if tag_name not in db_tags:
                        try:
                            self.db.save(self._process_tag(image, tag))
                        except ProcessingImageError as error:
                            self.log.warning(f'Metrics worker skip image: {error}')
            for tag_name in set(db_tags).difference(tags):
                image, tag = tag_name.split(':')
                self.db.remove(image, tag)

            self.db.update_stats(status=STATUSES.completed)
            self.log.debug('Metrics worker paused.')
        except KeyboardInterrupt:
            self.log.warning('Metrics worker stopped.')
            self.db.update_stats(status=STATUSES.error, error='stopped by user')
        except Exception as error:
            self.log.error(f'Metrics worker stopped with error: {error}')
            self.db.update_stats(status=STATUSES.error, error=str(error))

    def _process_tag(self, image: str, tag: str) -> t.Optional[Tag]:
        """
        Process a single tag.
        """
        try:
            self.log.debug(f'Processing {image}:{tag}')
            manifest = self._manifest(image, tag)

            _tag = Tag()
            _tag.digest = manifest['id']
            _tag.image = image
            _tag.tag = tag
            _tag.os = manifest['os']
            _tag.arch = manifest['architecture']
            _tag.created = manifest['created']
            _tag.layers = manifest['layers']

            return _tag
        except Exception as error:
            self.log.error(f"Error processing image {image}: {error}")
            raise ProcessingImageError(f'{image}:{tag}')

    def _catalog(self) -> t.Optional[t.List[str]]:
        """
        Get list of repositories from registry.
        """
        return self.registry.repositories()

    def _tags(self, image: str) -> t.List[str]:
        """
        Get tags for a specific image.
        """
        return self.registry.tags(image)

    def _manifest(self, image: str, tag: str) -> dict:
        """
        Get manifest for a specific image tag.
        """
        return self.registry.manifest(image, tag)

    def stats(self):
        """
        Return synchronization statistics.

        :return: timestamp, duration, status, and message
        """
        return self.db.stats()

    def size(self):
        """
        Return total size of registry (in bytes).

        :return: total size
        """
        return self.db.size()

    def images(self):
        """
        Return count of images.

        :return: count of images
        """
        return self.db.images()

    def layers(self):
        """
        Return count of layers.

        :return: count of tags
        """
        return self.db.layers()

    def dublicates(self):
        """
        Return list of image duplicates.

        :return: list of dublicates
        """
        return self.db.dublicates()

    def newest(self):
        """
        Return the most recently created tags.

        :return: list of tags
        """
        return self.db.newest()

    def oldest(self):
        """
        Return the oldest created tags.

        :return: list of tags
        """
        return self.db.oldest()

    def raw(self):
        """
        Return list of images with additional data (size, tags, created).

        :return: list of images
        """
        return self.db.raw()
