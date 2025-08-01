import typing as t
from hashlib import sha256
from re import findall

import requests
from flask import request
from flask import session
from hashlib import sha256
from requests.models import Response
from requests.structures import CaseInsensitiveDict
from werkzeug.exceptions import NotFound
from werkzeug.exceptions import Unauthorized

from drui.common.config import ConfigParser
from drui.common.logging import get_logger
from drui.common.utils import RequestParams
from drui.common.utils import check_status

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
        self.auth_providers = ('basic',)

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

    def request(self, method: str, uri: str, **kwargs: t.Any) -> Response:
        """
        Send HTTP request and return result.

        :param method: HTTP methods (GET, POST, PUT, etc.)
        :param uri: URI
        :param kwargs: additional request parameters
        :return: result of request
        """
        # # add user request headers to request
        headers = CaseInsensitiveDict(request.headers)
        headers.update(kwargs.pop('headers', {}))
        headers.pop('Content-Length', None)
        headers.pop('Cookie', None)
        headers.pop('User-Agent', None)
        headers.pop('Host', None)
        kwargs['headers'] = headers

        # # add auth credentials to request
        kwargs['auth'] = session.get('auth')

        return requests.request(method, self.registry_endpoint + uri, **kwargs)

    def login(self, username: str, password: str) -> bool:
        """
        User authorization in Registry.

        :param username: username
        :param password: user password
        :return: True if authorization complete successfully, else False
        """
        # get auth provider: basic, bearer, etc...
        # raise Unauthorized if provider not supported
        resp = self.request('GET', '/v2/')
        provider = auth_provider(resp)
        if provider not in self.auth_providers:
            raise Unauthorized(f'Auth provider "{provider}" not supported.')

        # save auth credentials in session
        session['auth'] = (username, password)
        session['provider'] = provider

        # check connection to registry with auth credentials
        resp = self.request('GET', '/v2/')
        check_status(resp)
        return True

    def repositories(self) -> t.List[str]:
        """
        Return repository list.
        """
        resp = self.request('GET', '/v2/_catalog')
        check_status(resp)
        return resp.json().get('repositories', [])

    def manifest(self, image: str, tag: str) -> t.Optional[t.Dict]:
        """
        Return image tag manifest.

        :param image: image name
        :param tag: image tag
        :return: manifest
        """
        params = RequestParams()
        ref = params.get('digest', default=tag)
        manifest = {}

        try:
            # get manifest list
            resp = self.request('GET', f'/v2/{image}/manifests/{tag}',
                                headers=self.accept)
            check_status(resp)

            manifest_list = resp.json().get('manifests')
            manifest['manifests'] = manifest_list

            if manifest_list:
                ref = manifest_list[0]['digest']
        except NotFound:
            pass

        # get image manifest
        try:
            resp = self.request('GET', f'/v2/{image}/manifests/{ref}',
                                headers=self.accept)
            check_status(resp)
        except NotFound:
            return None
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
