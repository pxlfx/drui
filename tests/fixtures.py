# -*- coding: utf-8 -*-

from importlib import reload
from os import environ
import pytest
from drui import app as drui_app
from drui.common import logging
from drui.common.config import ConfigParser
from .mock_registry import RegistryServer

# Port for mock_registry
MOCK_REGISTRY_PORT = 5432


def clear_env():
    """ Clear drui environment variables. """
    for key in list(environ):
        if key.upper().startswith('DRUI_'):
            environ.pop(key)


@pytest.fixture
def config(cache, request):
    """
    Return configuration file.

    :param cache: pytest cache instance
    :param request: environment dict from test
    :return: configuration file
    """
    rs = RegistryServer(port=MOCK_REGISTRY_PORT)
    logging_path = f'{cache.mkdir("logs")}/output'

    clear_env()
    environ.update({
        'DRUI_REGISTRY_ENDPOINT': rs.endpoint,
        'DRUI_LOGGING_FORMAT': '%(method)s %(status_code)s %(url)s',
        'DRUI_LOGGING_PATH': logging_path,
        **(request.param if hasattr(request, 'param') else {})
    })

    conf = ConfigParser(allow_no_value=True)
    yield conf


@pytest.fixture
def app(config):
    """
    Return drui instance.

    :param config: configuration file
    :return: drui
    """
    reload(drui_app)
    yield drui_app.init_app(config)


@pytest.fixture
def client(app, request):
    """
    Return test client.

    :param app: drui
    :param request: additional parameters for mock_registry
    :return: test client
    """
    kwargs = {
        'port': MOCK_REGISTRY_PORT,
        **(request.param if hasattr(request, 'param') else {})
    }
    rs = RegistryServer(**kwargs)
    rs.start()
    yield app.test_client()
    rs.stop()


@pytest.fixture
def log():
    return logging.get_logger(__name__)
