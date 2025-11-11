import typing as t
from hashlib import sha256
from io import BytesIO
from json import dumps
from re import findall

import requests
from flask import request
from flask import session
from requests import PreparedRequest
from requests.models import Response
from requests.structures import CaseInsensitiveDict
from werkzeug.exceptions import NotFound
from werkzeug.exceptions import NotImplemented
from werkzeug.exceptions import Unauthorized

from drui.common.config import ConfigParser
from drui.common.logging import get_logger
from drui.common.tarstream import TarStream
from drui.common.utils import RequestParams
from drui.common.utils import check_status
from drui.token import bearer_token

log = get_logger(__name__)


def union(*args) -> str:
    return ','.join(args)


def semver_comparison(version: str) -> list:
    """
    SemVer comparison.

    return 'latest' version in the end.
    """

    def to_number(text: str) -> list:
        if text.isnumeric():
            return [int(text)]
        return [ord(char) for char in text.upper()]

    if str(version).upper() == 'LATEST':
        return [float('inf')]

    chars = findall('\\w+', str(version))
    return sum(list(to_number(char) for char in chars), [])


def auth_provider(response: Response) -> t.Optional[str]:
    """
    Return response authentication provider.

    :param response: HTTP response
    :return: authentication provider
    """
    auth_header = response.headers.get('Www-Authenticate')
    return auth_header.lower().split()[0] if auth_header else None


class Registry:
    def __init__(self, conf: ConfigParser) -> None:
        """
        :param conf: configuration
        """
        self.conf = conf

        # supported authentication providers:
        #  - basic: apache htpasswd file
        self.auth_providers = ('basic', 'bearer',)

        # registry endpoint
        self.registry_endpoint = self.conf.get('endpoint', 'registry',
                                               default='')
        if not self.registry_endpoint:
            raise KeyError('Registry endpoint not set.'
                           ' Check configuraion file.')

        # api accept headers list
        self.accept = {
            'Accept': union(
                'application/vnd.oci.image.index.v1+json',
                'application/vnd.docker.distribution.manifest.list.v2+json',
                'application/vnd.docker.distribution.manifest.v2+json',
                'application/vnd.oci.image.manifest.v1+json'
            )
        }

    def make_request(self, **kwargs):
        kwargs['url'] = self.registry_endpoint + kwargs['uri']
        del kwargs['uri']

        # add user request headers to request
        headers = CaseInsensitiveDict(request.headers)
        headers.update(kwargs.pop('headers', {}))
        headers.pop('Content-Length', None)
        headers.pop('Cookie', None)
        headers.pop('User-Agent', None)
        headers.pop('Host', None)
        kwargs['headers'] = headers

        # add auth header to request
        if 'Authorization' not in headers:
            kwargs['auth'] = session.get('auth')

        req = requests.Request(**kwargs)
        return req.prepare()

    def request(self, method: str, uri: str, **kwargs: t.Any) -> Response:
        """
        Send HTTP request and return result.

        :param method: HTTP methods (GET, POST, PUT, etc.)
        :param uri: URI
        :param kwargs: additional request parameters
        :return: result of request
        """
        kwargs.update({'method': method, 'uri': uri})
        req = self.make_request(**kwargs)
        with requests.Session() as request_session:
            resp = request_session.send(req)

        try:
            check_status(resp)
        except Unauthorized:
            # get auth provider: basic, bearer, etc...
            # raise Unauthorized if provider not supported
            provider = auth_provider(resp)
            if provider not in self.auth_providers:
                raise Unauthorized(
                    f'Auth provider "{provider}" not supported.')

            if provider == 'bearer':
                token = bearer_token(resp)
                kwargs.setdefault('headers', {})
                kwargs['headers'].update({'Authorization': f'Bearer {token}'})
                return self.request(**kwargs)

        return resp

    def login(self, username: str, password: str) -> None:
        """
        User authorization in Registry.

        :param username: username
        :param password: user password
        """
        # save auth credentials in session
        session['auth'] = (username, password)

        # check access ro Registry
        resp = self.request('HEAD', '/v2/')
        check_status(resp)

    def repositories(self) -> t.List[str]:
        """
        Return repository list.
        """
        repository_list = []
        limit = 1000
        last = ''

        while True:
            resp = self.request('GET', f'/v2/_catalog?n={limit}&last={last}')
            check_status(resp)
            part_of_repository_list = resp.json().get('repositories', [])
            repository_list.extend(part_of_repository_list)
            if len(part_of_repository_list) < limit:
                break
            last = part_of_repository_list[-1]

        return repository_list

    def manifest(self, image: str, tag: str) -> t.Optional[t.Dict]:
        """
        Return image tag manifest.

        :param image: image name
        :param tag: image tag
        :return: manifest
        """
        params = RequestParams()
        digest = params.get('digest')
        manifest = {}

        resp = self.request('GET', f'/v2/{image}/manifests/{tag}',
                            headers=self.accept)
        check_status(resp)
        manifest.update(resp.json())

        # get manifest list
        manifest_list = resp.json().get('manifests')
        manifest['manifests'] = manifest_list

        if manifest_list and not digest:
            digest = manifest_list[0]['digest']

        # get manifest by digest
        if digest:
            resp = self.request('GET', f'/v2/{image}/manifests/{digest}',
                                headers=self.accept)
            check_status(resp)
            manifest.update(resp.json())

        # add image digest to manifest
        manifest['digest'] = resp.headers.get(
            'Docker-Content-Digest',
            default=sha256(resp.text.encode('utf-8')).hexdigest()
        )

        # add image configuration to manifest
        if 'config' not in manifest:
            log.warning(f'Unknown manifest: {manifest}')
            return None

        config_digest = manifest['config'].get('digest')
        resp = self.request('GET', f'/v2/{image}/blobs/{config_digest}',
                            headers=self.accept)
        check_status(resp)
        manifest.update(resp.json())

        # add image ID to manifest
        manifest['id'] = resp.headers.get('Docker-Content-Digest')
        return manifest

    def tags(self, image: str) -> t.Optional[t.List[str]]:
        """
        Return image tag list.

        :param image: image name
        :return: tags
        """
        try:
            resp = self.request('GET', f'/v2/{image}/tags/list')
            check_status(resp)
            return sorted(resp.json().get('tags', []), key=semver_comparison)
        except (NotFound, TypeError):
            return None

    def delete(self, image: str, tag: str) -> bool:
        """
        Delete image tag.

        :param image: image name
        :param tag: image tag
        :return:
        """
        manifest = self.manifest(image, tag)
        if not manifest:
            return False

        digest = manifest.get('digest')
        if not digest:
            return False

        resp = self.request('DELETE', f'/v2/{image}/manifests/{digest}',
                            headers=self.accept)
        check_status(resp)
        return True

    def blob(self, image: str, digest: str) -> PreparedRequest:
        """
        Prepare HTTP request for blob download.

        :param image: image name
        :param digest: blob digest
        """
        resp = self.make_request(
            method='GET',
            uri=f'/v2/{image}/blobs/{digest}',
            headers=self.accept
        )
        return resp

    def image_tar(self, image: str, tag: str):
        """
        Generate a Docker image TAR archive.

        Supported manifest version 2.

        Based on the official Moby implementation:
        https://github.com/moby/moby/blob/master/contrib/download-frozen-image-v2.sh

        :param image: image name
        :param tag: image tag
        :return: TarStream containing the complete image archive
        """
        stream = TarStream()

        manifest = self.manifest(image, tag)
        schema_version = manifest.get('schemaVersion')
        if schema_version != 2:
            raise NotImplemented(f'Manifest schemaVersion "{schema_version}'
                                 ' not supported.')

        # add image configuration
        config_digest = manifest.get('id')
        config_id = config_digest.split(':')[1]
        stream.add(
            self.blob(image, config_digest),
            filename=f'{config_id}.json'
        )

        # precompute VERSION file content (shared across all layers)
        version_content = b'1.0'

        # process image layers
        layers = manifest.get('layers', [])
        layer_entries = []
        parent_id = ''
        for layer in layers:
            layer_digest = layer.get('digest')
            layer_id = sha256(
                f'{parent_id}\n{layer_digest}\n'.encode()
            ).hexdigest()

            # add layer metadata file
            layer_json = {'id': layer_id}
            if parent_id:
                layer_json['parent'] = parent_id
            stream.add(
                BytesIO(dumps(layer_json).encode()),
                filename=f'{layer_id}/json'
            )

            # add layer VERSION file
            stream.add(
                BytesIO(version_content),
                filename=f'{layer_id}/VERSION'
            )

            # add layer data
            stream.add(
                self.blob(image, layer_digest),
                filename=f'{layer_id}/layer.tar'
            )

            # record layer ID for manifest
            layer_entries.append(f'{layer_id}/layer.tar')

        # add manifest file
        manifest_entry = [{
            'Config': f'{config_id}.json',
            'RepoTags': [f'{image}:{tag}'],
            'Layers': layer_entries
        }]
        stream.add(BytesIO(
            dumps(manifest_entry).encode()),
            filename='manifest.json'
        )

        # add repositories file
        repositories_entry = {image: {tag: ''}}
        stream.add(
            BytesIO(dumps(repositories_entry).encode()),
            filename='repositories'
        )

        return stream
