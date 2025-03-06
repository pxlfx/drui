from os import environ

import pytest


def test_read(config):
    """
    Test the read functionality.
    """
    assert config.read('config.example.cfg')


def test_has_section(config):
    """
    Test the has_section functionality.
    """
    assert not config.has_section('section')
    config.set('option', 'value', 'section')
    assert config.has_section('section')


def test_get(config):
    """
    Test the get functionality.
    """
    config.set('option', 'value', 'section')
    value = config.get('option', 'section')
    assert value == 'value'


def test_get_default(config):
    """
    Test the get functionality with a default value.
    """
    value = config.get('option', 'section', default='default')
    assert value == 'default'


def test_get_env(config):
    """
    Test the get functionality with environment variables.
    """
    assert not config.get('option', 'section')
    environ['DRUI_SECTION_OPTION'] = 'value'

    value = config.get('option', 'section')
    assert value == 'value'


def test_getboolean(config):
    """
    Test the getboolean functionality.
    """
    config.set('option', 'true', 'section')
    value = config.getboolean('option', 'section')
    assert value is True


@pytest.mark.parametrize('set_value', ['string', '123'])
def test_getboolean_filtered(config, set_value):
    """
    Test the getboolean functionality with non-boolean values.
    """
    config.set('option', set_value, 'section')
    value = config.getboolean('option', 'section')
    assert value is None


def test_test_getboolean_default(config):
    """
    Test the getboolean functionality with a default value.
    """
    value = config.getboolean('option', 'section', default=False)
    assert value is False


def test_getint(config):
    """
    Test the getint functionality.
    """
    config.set('option', '123', 'section')
    value = config.getint('option', 'section')
    assert value == 123


@pytest.mark.parametrize('set_value', [
    'string', 'true', 'false', '123_string'
])
def test_getint_filtered(config, set_value):
    """
    Test the getint functionality with non-integer values.
    """
    config.set('option', set_value, 'section')
    value = config.getint('option', 'section')
    assert value is None


def test_test_getint_default(config):
    """
    Test the getint functionality with a default value.
    """
    value = config.getboolean('option', 'section', default=123)
    assert value == 123


def test_getlist(config):
    """
    Test the getlist functionality.
    """
    config.set('option', '1, 2', 'section')
    value = config.getlist('option', 'section')
    assert value == ['1', '2']


@pytest.mark.parametrize('set_value', ['string', 'true', 'false'])
def test_getlist_filtered(config, set_value):
    """
    Test the getlist functionality with non-list values.
    """
    config.set('option', set_value, 'section')
    value = config.getlist('option', 'section')
    assert isinstance(value, list)


def test_test_getlist_default(config):
    """
    Test the getlist functionality with a default value.
    """
    value = config.getlist('option', 'section', default=[1, 2])
    assert value == [1, 2]


def test_getlist_multiline(config):
    """
    Test the getlist multiline functionality.
    """
    config.set('option', '1, 2,\n3, 4', 'section')
    value = config.getlist('option', 'section')
    assert value == ['1', '2', '3', '4']
