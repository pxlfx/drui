# Docker distribution mock server.
# Support minimal API v2
# https://distribution.github.io/distribution/spec/api/

import typing as t
from json import loads
from multiprocessing import Process
from os.path import exists
from time import sleep

import flask
from flask import jsonify
from requests import request
from requests.exceptions import ConnectionError


class RegistryServer:
    def __init__(self, port: int = 5432, auth: bool = False):
        """
        :param port: port for listening
        :param auth: enable authentication
        """
        self.process = None
        self.protocol = 'http'
        self.host = 'localhost'
        self.port = port
        self.endpoint = f'{self.protocol}://{self.host}:{self.port}'
        self.auth = auth
        self.app = flask.Flask(__name__)

        # API rules
        self.app.before_request(self.check_auth)

        self.app.add_url_rule('/v2/', view_func=self.base)
        self.app.add_url_rule('/v2/_catalog', view_func=self.catalog)
        self.app.add_url_rule('/v2/<path:image>/tags/list', view_func=self.tags)
        self.app.add_url_rule('/v2/<path:image>/manifests/<digest>', view_func=self.manifest)
        self.app.add_url_rule('/v2/<path:image>/blobs/<digest>', view_func=self.blob)
        self.app.add_url_rule('/v2/<path:image>/manifests/<digest>',view_func=self.delete, methods=['DELETE'])

    def start(self):
        """
        Start server.
        """
        self.process = Process(target=self.app.run,
                               args=(self.host, self.port),
                               daemon=True)
        self.process.start()

        for _ in range(5):
            try:
                request('HEAD', f'{self.endpoint}/v2')
                return
            except ConnectionError:
                sleep(0.1)

    def stop(self):
        """
        Stop server.
        """
        self.process.terminate()
        self.process.join()

    @staticmethod
    def response(data: t.Any = None, headers: t.Optional[t.Dict] = None, status_code: int = 200) -> flask.Response:
        """
        Prepare and return HTTP response.

        :param data: response data
        :param headers: HTTP headers
        :param status_code: HTTP status code
        :return: HTTP response
        """
        resp = jsonify(data)
        resp.headers.update({'docker-distribution-api-version': 'registry/2.0'})
        resp.headers.update(headers if headers else {})
        resp.status_code = status_code
        return resp
    
    def _read_json_file(self, path: str) -> flask.Response:
        """
        Read JSON file and return response.

        :param path: path to data
        :retrun: data content
        """
        with open(path, 'r') as file:
            data = loads(file.read())
        return self.response(data)

    def check_auth(self):
        """
        Check request for auth credentials.
        """
        if self.auth and 'Authorization' not in flask.request.headers:
            return self.response(status_code=401, headers={'Www-Authenticate': 'Basic realm=""'})
        return None

    def base(self):
        """
        API version check.
        """
        return self.response()

    def catalog(self) -> flask.Response:
        """
        Return list of repositories.
        """
        return self.response({'repositories': ['docker.io/distribution']})

    def tags(self, image: str) -> flask.Response:
        """
        Return list of image tags.

        :param image: image name
        :return: tags
        """
        path = f'tests/data/repositories/{image}/tags.json'
        if not exists(path):
            return self.response(status_code=404)
        return self._read_json_file(path)

    def manifest(self, image: str, digest: str) -> flask.Response:
        """
        Return manifest.

        :param image: image name
        :param digest: content digest
        :return: manifest
        """
        m_index = 'application/vnd.oci.image.index.v1+json'
        m_list = 'application/vnd.docker.distribution.manifest.list.v2+json'
        m_v1 = 'application/vnd.oci.image.manifest.v1+json'
        m_v2 = 'application/vnd.docker.distribution.manifest.v2+json'

        path = None
        accept = flask.request.headers.get('Accept')
        if (m_index in accept and m_list in accept) or m_v1 in accept:
            path = f'tests/data/repositories/{image}/{digest}/v1.json'
        if m_v2 in accept:
            path = f'tests/data/repositories/{image}/{digest}/v2.json'

        if not exists(path):
            return self.response(status_code=404)

        data = self._read_json_file(path).json
        digest = data.get('config', {}).get('digest')
        return self.response(data, headers={'Docker-Content-Digest': digest})

    def blob(self, image: str, digest: str):
        """
        Return blob.

        :param image: image name
        :param digest: content digest
        :return: blob
        """
        short_digest = digest.replace('sha256:', '')[:12]
        path = f'tests/data/blobs/{short_digest}.json'
        if not exists(path):
            return self.response(f'{image}:{digest} not found', status_code=404)
        return self._read_json_file(path)

    def delete(self, image: str, digest: str):
        """
        Delete image tag.

        :param image: image name
        :param digest: content digest
        :return:
        """
        short_digest = digest.replace('sha256:', '')[:12]
        path = f'tests/data/blobs/{short_digest}.json'
        if not exists(path):
            return self.response(status_code=404)
        return self.response(f'{image}:{digest} successfully deleted')
    