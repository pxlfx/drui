import re
import typing as t
from urllib.parse import urlparse

import requests
from flask import g
from flask import session
from werkzeug.exceptions import ServiceUnavailable

from drui.common.utils import check_status


def extract_realm(auth_header: str) -> t.Tuple[str, t.Dict[str, str]]:
    """
    Extract realm parameters from auth header.

    Auth header example: "Bearer realm='https://example.com', scope='read'"

    :param auth_header: HTTP auth header
    :return: tuple with realm URL and realm parameters
    :raises ValueError: if header is invalid or realm not found
    """
    if not auth_header.strip().startswith('Bearer'):
        raise ValueError('Invalid WWW-Authenticate header:'
                         ' missing Bearer scheme.')

    params_str = auth_header[len('Bearer'):].lstrip()
    if not params_str:
        raise ValueError('Invalid WWW-Authenticate header:'
                         ' missing parameters.')

    params = {}
    param_pattern = re.compile(r'(\w+)\s*=\s*"([^"]*)"')

    for match in param_pattern.finditer(params_str):
        key, value = match.groups()
        params[key] = value

    realm = params.pop('realm', None)
    if not realm:
        raise ValueError('Realm parameter not found in'
                         ' WWW-Authenticate header.')

    try:
        parsed_realm = urlparse(realm)
        if not parsed_realm.scheme:
            realm = f'https://{realm}'
    except Exception as error:
        raise ValueError(f'Invalid realm URL: {realm}.') from error

    return realm, params


def bearer_token(resp: requests.Response, cache: bool = True) -> str:
    """
    Get Bearer Token for request.

    :param resp: HTTP response with WWW-Authenticate header
    :param cache: use cache
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

    tokens: t.Dict[str, str] = session.get('tokens', {})
    scope = params.get('scope', '')
    current_scope = g.get('token_scope')
    g.setdefault('token_scope', scope)

    # remove old token if request scope is a current scope
    if scope == current_scope:
        del tokens[current_scope]

    if cache and scope in tokens:
        return tokens[scope]

    try:
        response = requests.get(realm_url, params=params, auth=session['auth'])
        response.raise_for_status()

        token_data = response.json()
        token = token_data.get('token')
        if not token:
            raise ValueError(f'Token not found in response: {token_data}.')
        tokens[scope] = token
    except (requests.RequestException, ValueError, KeyError):
        resp.status_code = 401
        check_status(resp)

    session['tokens'] = tokens
    return tokens[scope]
