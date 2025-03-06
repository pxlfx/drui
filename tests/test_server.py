# -*- coding: utf-8 -*-

import re
from collections import defaultdict

import pytest
from bs4 import BeautifulSoup

# snapshot for URL rules and their corresponding methods
url_map_snapshot = {
    '/': {'GET', 'HEAD', 'OPTIONS'},
    '/r/<path:name>': {'GET', 'HEAD', 'OPTIONS'},
    '/_/<path:image>': {'GET', 'HEAD', 'OPTIONS'},
    '/_/<path:image>/tags/<tag>': {'GET', 'HEAD', 'OPTIONS', 'DELETE'},
    '/login': {'POST', 'OPTIONS'},
    '/logout': {'GET', 'HEAD', 'OPTIONS'},
    '/broadcast': {'GET', 'HEAD', 'OPTIONS'},
    '/static/<path:filename>': {'GET', 'HEAD', 'OPTIONS'},
}

# path to file with broadcast message
broadcast_path = 'tests/data/broadcast.md'


def get_script(pattern, text):
    soup = BeautifulSoup(text, 'html.parser')
    return soup.find('script', string=pattern)


def assert_response(response, status_code=200, json_check=False):
    assert response.status_code == status_code
    if json_check:
        assert response.json
    response.close()


def test_missing_rules(app):
    """
    Test for missing rules.

    This test ensures that all URL rules and their corresponding HTTP methods
    are correctly registered in the application. It compares the current URL
    rules and methods with a predefined snapshot to verify consistency.
    """
    rules = defaultdict(set)
    for r in app.url_map.iter_rules():
        rules[r.rule].update(r.methods)

    assert url_map_snapshot == dict(rules)


def test_catalog(client):
    """
    Test the catalog endpoint.
    """
    response = client.get('/')
    assert_response(response)

    pattern = re.compile(r'const repositories = (.*);')
    script = get_script(pattern, response.text)
    assert script
    assert pattern.search(script.text).group(1) == '["docker.io/distribution"]'


def test_catalog_json(client):
    """
    Test the catalog endpoint with JSON format.
    """
    response = client.get('/', data={'format': 'json'})
    assert_response(response, json_check=True)


def test_repository(client):
    """
    Test the repository endpoint.
    """
    response = client.get('/r/docker.io')
    assert_response(response)

    pattern = re.compile(r'const repositories = (.*);')
    script = get_script(pattern, response.text)
    assert script
    assert pattern.search(script.text).group(1) == '["docker.io/distribution"]'


def test_repository_json(client):
    """
    Test the repository endpoint with JSON format.
    """
    response = client.get('/r/docker.io', data={'format': 'json'})
    assert_response(response, json_check=True)


def test_image(client):
    """
    Test the image endpoint.
    """
    response = client.get('/_/docker.io/distribution/tags/latest')
    assert_response(response)

    pattern = re.compile(r'const image = (.*);')
    script = get_script(pattern, response.text)
    assert script
    assert pattern.search(script.text).group(1) == '"docker.io/distribution"'


def test_image_json(client):
    """
    Test the image endpoint with JSON format.
    """
    response = client.get(
        '/_/docker.io/distribution/tags/latest', data={'format': 'json'})
    assert_response(response, json_check=True)


def test_image_ref(client):
    """
    Test the image reference endpoint.
    """
    response = client.get('/_/docker.io/distribution')
    assert_response(response, status_code=302)


@pytest.mark.parametrize('uri', ['/_/non-exist', '/_/non-exist/tags/latest'])
def test_missing_manifest(uri, client):
    """
    Test for missing manifest.
    """
    response = client.get(uri)
    assert_response(response)

    soup = BeautifulSoup(response.text, 'html.parser')
    info = soup.find('div', class_='alert alert-info').find('b')
    assert info
    assert info.text == 'Repository is empty.'


def test_delete_image_tag(client):
    """
    Test deleting an image tag.
    """
    response = client.delete('/_/docker.io/distribution/tags/latest')
    assert_response(response)


@pytest.mark.parametrize('config',
                         [{'DRUI_DISABLE_DELETE': 'true'}],
                         indirect=True)
def test_disable_delete_image_tag(config, client):
    """
    Test disabling the deletion of image tags.
    """
    response = client.delete('/_/docker.io/distribution/tags/latest')
    assert_response(response, status_code=405)


@pytest.mark.parametrize('client', [{'auth': True}], indirect=True)
def test_check_auth(client):
    """
    Test authentication.
    """
    response = client.get('/')
    assert_response(response, status_code=401)


@pytest.mark.parametrize('client', [{'auth': True}], indirect=True)
def test_login(client):
    """
    Test login functionality.
    """
    response = client.post('/login', data={'username': 'u', 'password': 'p'})
    assert_response(response, status_code=302)


@pytest.mark.parametrize('client', [{'auth': True}], indirect=True)
def test_bad_login(client):
    """
    Test bad login attempt.
    """
    response = client.post('/login', data={'username': 'u'})
    assert_response(response, status_code=401)


@pytest.mark.parametrize('client', [{'auth': True}], indirect=True)
def test_logout(client):
    """
    Test logout functionality.
    """
    response = client.post('/login', data={'username': 'u', 'password': 'p'})
    assert_response(response, status_code=302)

    client.get('/logout')
    response = client.get('/')
    assert_response(response, status_code=401)


@pytest.mark.parametrize('config',
                         [{'DRUI_BROADCAST_PATH': broadcast_path}],
                         indirect=True)
def test_broadcast(config, client):
    """
    Test broadcast message functionality.
    """
    response = client.get('/broadcast')
    assert_response(response, json_check=True)


@pytest.mark.parametrize('config',
                         [{'DRUI_BROADCAST_PATH': 'wrong_data'}],
                         indirect=True)
def test_bad_broadcast(config, client):
    """
    Test bad broadcast configuration.
    """
    response = client.get('/broadcast')
    assert_response(response, status_code=404)


def test_404_page(client):
    """
    Test 404 error page.
    """
    response = client.get('/test')
    assert_response(response, status_code=404)

    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.find('title')
    assert title
    assert title.text == 'Not Found (404)'


def test_404_page_json(client):
    """
    Test 404 error page with JSON format.
    """
    response = client.get('/test', data={'format': 'json'})
    assert_response(response, status_code=404, json_check=True)
