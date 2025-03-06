# -*- coding: utf-8 -*-

import logging
import sys
import typing as t

from flask import Flask
from flask import has_request_context
from flask import request

from . import config

NOTSET = logging.NOTSET
conf = config.CONF


class RequestFormatter(logging.Formatter):
    def __init__(self, *args, **kwargs):
        self.default_value = '-'
        datefmt = conf.get('date_format', section='logging',
                           default='%Y-%m-%d %H:%M:%S')
        super().__init__(*args, datefmt=datefmt, **kwargs)

    def _get_header(self, key: str) -> t.Optional[str]:
        return request.headers.get(key, default=self.default_value)

    def format(self, record):
        if has_request_context():
            url = request.full_path if request.query_string else request.path

            record.url = url
            record.method = request.method
            record.remote_addr = request.remote_addr
            record.status_code = request.environ.get('status_code')
            record.user_agent = self._get_header('User-Agent')
            record.referer = self._get_header('Referer')
            record.x_forwarded_for = self._get_header('X-Forwarded-For')
            record.content_length = request.environ.get('content_length')
        else:
            record.url = self.default_value
            record.method = self.default_value
            record.remote_addr = self.default_value
            record.status_code = self.default_value
            record.user_agent = self.default_value
            record.referer = self.default_value
            record.x_forwarded_for = self.default_value
            record.content_length = self.default_value

        return super().format(record)


def disable_wsgi_logging(app: Flask) -> None:
    """
    Setting up logging parameters.

    :param app: Flask-app instance
    """
    # set logging level
    app.logger.setLevel(logging.INFO)

    # disable web server logging
    logging.getLogger('werkzeug').disabled = True
    logging.getLogger('urllib3.connectionpool').disabled = True

    # disable the initial message from Flask
    cli = sys.modules.get('flask.cli')
    if cli:
        cli.show_server_banner = lambda *x: None


def get_logger(name: t.Optional[str] = None) -> logging.Logger:
    """
    Return an instance of the Logger class.

    Simulates the behavior of logging.getLogger.

    :param name: <ignoring>
    :returns: logging handler
    """
    formatter = RequestFormatter('[%(asctime)s] %(levelname)s %(method)s'
                                 ' %(status_code)s %(url)s %(message)s')

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    path = conf.get('path', section='logging')
    handler = logging.FileHandler(path) if path else logging.StreamHandler()
    handler.setLevel(logging.DEBUG)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
