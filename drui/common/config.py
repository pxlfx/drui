# -*- coding: utf-8 -*-

import typing as t
from configparser import ConfigParser as _ConfigParser
from configparser import DEFAULTSECT
from configparser import NoOptionError
from configparser import NoSectionError
from functools import wraps
from os import PathLike
from os import environ


def get_env(func: t.Callable) -> t.Callable:
    """
    Decorator: return variable from environment.
    """

    def env_key(option: str, section: str = DEFAULTSECT) -> str:
        """
         Converts the name of the requested variable to the corresponding
         environment variable name.

        :param option: option name
        :param section: section
        :return: environment variable name
        """
        prefix = 'drui'
        if section != DEFAULTSECT:
            return f'{prefix}_{section}_{option}'.upper()
        return f'{prefix}_{option}'.upper()

    @wraps(func)
    def wrapper(*args: t.Any, **kwargs: t.Any) -> t.Any:
        self, option, *section = args

        if not section and 'section' in kwargs:
            section = [kwargs.get('section', '')]

        key = env_key(option, *section)
        if key in environ:
            self.set(option, environ.get(key), *section)

        return func(*args, **kwargs)

    return wrapper


class ConfigParser:
    def __init__(self, **kwargs: t.Any) -> None:
        self._config = _ConfigParser(**kwargs)

    def read(self, config_file: t.Union[PathLike]) -> t.List[str]:
        return self._config.read(config_file, encoding='utf-8')

    def add_section(self, section: str) -> None:
        return self._config.add_section(section)

    def has_section(self, section: str) -> bool:
        return self._config.has_section(section)

    def set(
            self,
            option: str,
            value: str,
            section: str = DEFAULTSECT
    ) -> None:
        try:
            return self._config.set(section, option, value)
        except NoSectionError:
            self.add_section(section)
            return self._config.set(section, option, value)

    @get_env
    def get(
            self,
            option: str,
            section: str = DEFAULTSECT,
            default: t.Optional[str] = None
    ) -> t.Optional[str]:
        try:
            v = self._config.get(section, option, raw=True)
            return v if v else default
        except (NoOptionError, NoSectionError, ValueError):
            return default

    @get_env
    def getboolean(
            self,
            option: str,
            section: str = DEFAULTSECT,
            default: t.Optional[bool] = None
    ) -> t.Optional[bool]:
        try:
            return self._config.getboolean(section, option)
        except (NoOptionError, NoSectionError, ValueError):
            return default

    @get_env
    def getint(
            self,
            option: str,
            section: str = DEFAULTSECT,
            default: t.Optional[int] = None
    ) -> t.Optional[int]:
        try:
            return self._config.getint(section, option)
        except (NoOptionError, NoSectionError, ValueError):
            return default

    @get_env
    def getlist(
            self,
            option: str,
            section: str = DEFAULTSECT,
            default: t.Optional[t.List] = None
    ) -> t.Optional[t.List]:
        try:
            _ = self._config.get(section, option, raw=True)
            if not _.strip():
                return default
            return list(map(lambda x: x.strip(), _.replace(' ', '').split(',')))
        except (NoOptionError, NoSectionError, ValueError):
            return default


CONF = ConfigParser(allow_no_value=True)
