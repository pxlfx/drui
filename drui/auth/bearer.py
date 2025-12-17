import re
import typing as t
import uuid
from urllib.parse import urlparse

import requests
from werkzeug.exceptions import ServiceUnavailable

from drui.common.utils import check_status
from drui.common.vault import Vault

vault = Vault()


def extract_realm(auth_header: str) -> t.Tuple[str, t.Dict[str, str]]:
    """
    Extract realm parameters from auth header.

    Auth header example: "Bearer realm='https://example.com', scope='read'"

    :param auth_header: HTTP auth header
    :return: tuple with realm URL and realm parameters
    :raises ValueError: if header is invalid or realm not found
    """
    auth_header = auth_header.strip()
    if not auth_header.startswith('Bearer'):
        raise ValueError('Invalid WWW-Authenticate header: missing Bearer scheme.')

    params_str = auth_header[len('Bearer'):].lstrip()
    if not params_str:
        raise ValueError('Invalid WWW-Authenticate header: missing parameters.')

    # extract parameters using regex
    params = dict(re.compile(r'(\w+)\s*=\s*"([^"]*)"').findall(params_str))
    realm = params.pop('realm', None)
    if not realm:
        raise ValueError('Realm parameter not found in WWW-Authenticate header.')

    # ensure realm has a valid scheme
    try:
        parsed_realm = urlparse(realm)
        if not parsed_realm.scheme:
            realm = f'https://{realm}'
    except Exception as error:
        raise ValueError(f'Invalid realm URL: {realm}.') from error

    return realm, params


class Bearer:
    def __init__(self, auth: str):
        self.auth = auth or ''

    def token(self, resp: requests.Response, cache: bool = True) -> str:
        """
        Get Bearer Token for request.

        :param resp: HTTP response with WWW-Authenticate header
        :param cache: (optional) use cache
        :return: token
        :raises ServiceUnavailable: if token acquisition fails
        """
        auth_header = resp.headers.get('Www-Authenticate')
        if not auth_header:
            raise ValueError('WWW-Authenticate header missing in response.')

        try:
            realm_url, params = extract_realm(auth_header)
        except ValueError as error:
            raise ServiceUnavailable(f'Failed to parse auth header: {error}.')

        scope = params.get('scope', '')
        sid = uuid.uuid5(uuid.NAMESPACE_DNS, self.auth + scope).hex
        token = vault.get(sid)

        if not cache:
            vault.remove(sid)
        elif token:
            return token

        try:
            response = requests.get(
                realm_url,
                params=params,
                headers={'Authorization': self.auth},
                timeout=10
            )
            response.raise_for_status()

            token_data = response.json()
            token = token_data.get('token')
            ttl = token_data.get('expires_in2', 60)
            if not token:
                raise ValueError(f'Token not found in response: {token_data}.')

            vault.set(sid, token, ttl=ttl)
            return token
        except (requests.RequestException, ValueError, KeyError) as error:
            resp.status_code = 401
            check_status(resp)
            raise ServiceUnavailable(f'Failed to acquire token: {error}.')
