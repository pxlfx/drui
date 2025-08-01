import os
import typing as t
from re import match
from re import sub

import flask
from werkzeug import Response
from werkzeug.exceptions import HTTPException
from werkzeug.exceptions import Unauthorized
from werkzeug.middleware.proxy_fix import ProxyFix

from drui import __version__
from drui.common.config import ConfigParser
from drui.common.logging import RequestFormatter
from drui.common.logging import disable_wsgi_logging
from drui.common.logging import get_logger
from drui.common.utils import RequestParams
from drui.common.utils import json_answer
from drui.common.utils import to_json
from drui.middleware import check_response
from drui.registry import Registry

app = flask.Flask(__name__)
log = get_logger(__name__)


def get_registry() -> Registry:
    """
    Return Registry instance.
    """
    return getattr(flask.current_app, 'registry')


def get_conf() -> ConfigParser:
    """
    Return ConfigParser instance.
    """
    return getattr(flask.current_app, 'conf')


@app.route('/')
def catalog() -> t.Union[Response, str]:
    """
    Return image list.
    """
    registry = get_registry()
    repository_list = registry.repositories()

    if to_json():
        return json_answer(repository_list)
    return flask.render_template('repositories.html',
                                 repositories=repository_list)


@app.route('/r/<path:name>')
def repository(name) -> t.Union[Response, str]:
    """
    Return image list, filtered by repository name.

    :param name: repository name
    :return: image list
    """
    registry = get_registry()
    rl = registry.repositories()
    repository_list = list(filter(lambda x: x.startswith(name), rl))

    if to_json():
        return json_answer(repository_list)
    return flask.render_template('repositories.html',
                                 repository=name,
                                 repositories=repository_list)


@app.route('/_/<path:image>')
def image_ref(image: str) -> t.Union[Response, str]:
    """
    Refer to image tag page.

    :param image: image name
    """
    registry = getattr(flask.current_app, 'registry')
    tags = registry.tags(image)
    if not tags:
        return flask.render_template('empty.html', image=image)
    tag = 'latest' if (not tags or 'latest' in tags) else tags[-1]

    return flask.redirect(f'/_/{image}/tags/{tag}')


@app.route('/_/<path:image>/tags/<tag>')
def image_tag(image: str, tag: str) -> t.Union[Response, str]:
    """
    Return information about image tag.

    :param image: image name
    :param tag: tag name
    :return: information about image tag
    """
    registry = getattr(flask.current_app, 'registry')
    endpoint = registry.conf.get('endpoint', 'registry')
    pull_endpoint = registry.conf.get('pull_endpoint', 'registry',
                                      default=endpoint)

    # get image manifest
    manifest = registry.manifest(image, tag)
    if not manifest:
        return flask.render_template('empty.html', image=image)

    # get image tags
    tags = registry.tags(image)

    if to_json():
        return json_answer({'tags': tags, 'manifest': manifest})
    return flask.render_template('image.html',
                                 image=image,
                                 tags=tags,
                                 tag=tag,
                                 manifest=manifest)


@app.route('/_/<path:image>/tags/<tag>', methods=['DELETE'])
def image_tag_delete(image: str, tag: str) -> Response:
    """
    Delete image tag.

    :param image: image name
    :param tag: image tag
    :return: Docker Registry response
    """
    conf = getattr(flask.current_app, 'conf')
    if conf.getboolean('disable_delete'):
        flask.abort(405)

    registry = get_registry()
    result = registry.delete(image, tag)
    if not result:
        return json_answer(f'{image}:{tag} not found', status_code=404)
    return json_answer(f'{image}:{tag} successfully deleted')


def error_page(error: HTTPException) -> t.Union[Response, t.Tuple[str, int]]:
    """
    Error page.

    :param error: python exception
    """
    if not hasattr(error, 'code'):
        error.code = 500
        error.description = """We're sorry, but something went wrong.
        We've been notified about this issue and we'll take
        a look at it shortly."""

    if to_json():
        return json_answer(error.description, status_code=error.code)
    return flask.render_template('error.html', error=error), error.code


@app.route('/login', methods=['POST'])
def login() -> t.Union[Response, t.Tuple[str, int]]:
    """
    User authorization.
    """
    params = RequestParams()
    username = params.get('username')
    password = params.get('password')
    if not username or not password:
        return flask.render_template('login.html', error=Unauthorized()), 401

    registry = get_registry()
    registry.login(username, password)

    return flask.redirect('/')


@app.route('/logout')
def logout() -> flask.Response:
    """
    Close user session.
    """
    flask.session.clear()
    return flask.redirect('/')


@app.route('/broadcast')
def get_broadcast() -> t.Union[Response, str]:
    """
    Return broadcast message.
    """
    conf = get_conf()
    path = conf.get('path', 'broadcast')

    if not path or not os.path.exists(path):
        return flask.make_response('Broadcast file not found.', 404)

    try:
        with open(path, 'r') as f:
            broadcast = f.read()
        return json_answer(broadcast)
    except Exception as error:
        return json_answer(str(error), status_code=500)


@app.template_global('get_repository')
def get_repository(image: str) -> t.Optional[str]:
    """
    Return image repository name.

    :param image: image name
    :return: repository name
    """
    match_result = match(r'(^.*)/(.*)', image)
    return match_result.group(1) if match_result else None


@app.template_global('get_application')
def get_application(image: str) -> t.Optional[str]:
    """
    Return image application name.

    :param image: image name
    :return: application name
    """
    match_result = match(r'(^.*)/(.*)', image)
    return match_result.group(2) if match_result else image


@app.template_global('get_endpoint')
def get_endpoint():
    """
    Return registry endpoint.
    """
    conf = get_conf()
    endpoint = conf.get('endpoint', 'registry', default='')
    endpoint = conf.get('pull_endpoint', 'registry', default=endpoint)
    return sub(r'^http[s]?://', '', endpoint)


@app.after_request
def log_after_request(response: flask.Response) -> flask.Response:
    """
    Request logging.

    :param response: HTTP response
    :return: HTTP response
    """

    @response.call_on_close
    @flask.copy_current_request_context
    def call_on_close():
        if not flask.request.path.startswith('/static/') and \
                flask.request.path not in ['/favicon.ico', '/broadcast']:
            flask.request.environ['status_code'] = response.status_code
            flask.request.environ['content_length'] = response.content_length

            if response.status_code >= 400:
                log.error(response.status)
            else:
                log.info('')

    return response


@app.context_processor
def inject_conf() -> dict:
    """
    Inject configuration into all templates.
    """
    return {'conf': get_conf()}


def app_version() -> str:
    """
    Return drui version.

    :return: version
    """
    return __version__


def init_app(conf: ConfigParser) -> flask.Flask:
    """
    Prepare Flask app for running.

    :param conf: instance of configuration file
    :return: instance of Flask app
    """
    setattr(app, 'conf', conf)
    setattr(app, 'registry', Registry(conf))
    app.secret_key = conf.get('secret_key', default='secret_key')

    # error codes registration
    for code in [400, 401, 403, 404, 405, 500, 503]:
        app.register_error_handler(code, error_page)

    # middlewares registration
    app.before_request_funcs = {None: [check_response.middleware]}

    # add drui version to template
    app.add_template_global(app_version, 'app_version')

    # add check session keys to template
    app.add_template_global(lambda x: x in flask.session, 'in_session')

    # disable Flask logging
    disable_wsgi_logging(app)

    # set logging format
    log_format = conf.get('format', section='logging')
    if log_format:
        for handler in log.handlers:
            formatter = RequestFormatter(log_format)
            handler.setFormatter(formatter)

    # add ProxyFix module for reverse proxy support
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1,
                            x_port=1, x_prefix=1)

    return app
