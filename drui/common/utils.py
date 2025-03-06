# -*- coding: utf-8 -*-

import logging
import typing as t

from flask import jsonify
from flask import request
from requests.models import Response
from werkzeug.exceptions import HTTPException
from werkzeug.exceptions import default_exceptions

log = logging.getLogger(__name__)


def check_status(resp: t.Optional[Response]) -> None:
    """
    Check response status code and raise exception at error.
    """
    if resp.status_code in default_exceptions:
        raise default_exceptions[resp.status_code](description=resp.reason)
    resp.raise_for_status()


def json_answer(message: t.Any, status_code: int = 200) -> Response:
    """
    Returns correctly formed data for transmission in JSON format.
    
    :param message: data in any format
    :param status_code: response status code
    :return: response in JSON
    """
    if isinstance(message, HTTPException):
        status_code = message.code
        message = message.description

    response = jsonify(message)
    response.status_code = status_code
    return response


class RequestParams:
    """
    Processing request parameters.
    """

    def __init__(self):
        self.params: t.Dict[str, t.Any] = {}
        lists = list(request.form.lists()) + list(request.args.lists())

        for key, value in lists:
            _key = key.replace('[]', '').lower()
            _value = value[0] if len(value) == 1 else value
            self.params[_key] = _value

    def __contains__(self, key: str) -> bool:
        """
        Checks if the specified key exists.

        :param key: key
        :returns: True - if key exist, else False
        """
        return key.lower() in self.params

    def get(self, key: str, default=None):
        """
        Return the value by key or default.

        :param key: key
        :param default: default value if key does not exist
        :return: value or default
        """
        return self.params.get(key.lower(), default)


def to_json() -> bool:
    """
    Returns True if data is requested in JSON format.
    """
    params = RequestParams()
    return params.get('format') == 'json'
