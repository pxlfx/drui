import typing as t

from flask import Response
from flask import current_app
from flask import render_template
from flask import request
from flask import session
from requests.exceptions import ConnectionError
from werkzeug.exceptions import HTTPException
from werkzeug.exceptions import InternalServerError
from werkzeug.exceptions import MethodNotAllowed
from werkzeug.exceptions import NotFound
from werkzeug.exceptions import ServiceUnavailable
from werkzeug.exceptions import Unauthorized
from werkzeug.routing import RequestRedirect
from werkzeug.routing import Rule

from drui.common.logging import get_logger
from drui.common.utils import json_answer
from drui.common.utils import to_json

log = get_logger(__name__)


def _prepare_error(error: Exception) -> t.Union[Response, t.Tuple[str, int]]:
    """
    Preparing an error for return.

    :param: error - error
    """
    if isinstance(error, ConnectionError):
        error = ServiceUnavailable()
    elif not isinstance(error, HTTPException):
        error = InternalServerError()

    if to_json():
        return json_answer(error)
    return render_template('core.html', error=error), error.code


def _get_view_func(url: t.Union[Rule, str],
                   method: str = 'GET') -> t.Optional[t.Tuple]:
    """
    Return the function to call for the specified URL and method.

    :param url: URL
    :param method: method
    :returns: function, function parameters
    """
    adapter = current_app.url_map.bind('localhost')

    try:
        match = adapter.match(url.rule, method=method)
    except RequestRedirect as e:
        return _get_view_func(e.new_url, method)
    except (MethodNotAllowed, NotFound):
        return None

    try:
        return current_app.view_functions[match[0]], match[1]
    except KeyError:
        return None


def middleware() -> t.Union[Response, t.Tuple[str, int], None]:
    """
    Intercept a request processing error and display it in HTML or JSON.
    """
    if request.path.startswith('/static/') or not request.url_rule:
        return None

    func, params = _get_view_func(request.url_rule, request.method)
    kwargs = request.view_args or {}

    try:
        return func(**kwargs) if func else None
    except Unauthorized as error:
        session.clear()
        if to_json():
            return json_answer(Unauthorized())
        return render_template('login.html', error=error), 401

    except Exception as error:
        log.warning(error)
        return _prepare_error(error)
