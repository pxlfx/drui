#!/usr/bin/env python3

import argparse
import atexit
import sys
from multiprocessing import set_start_method
from multiprocessing import Process
from multiprocessing import util
from os import environ
from os.path import abspath

from flask import Flask
from waitress import serve

from drui import __version__
from drui import metrics
from drui.app import init_app
from drui.common.config import CONF


# setting the 'fork' mode for multiprocessing in Python 3.14,
# is necessary for proper handling of the configuration file
try:
    set_start_method('fork', force=True)
except ValueError:
    pass


class WSGIApplication:
    """
    Custom class for Waitress application.
    """

    def __init__(self, app, host='0.0.0.0', port=8000, threads=8):
        self.app = app
        self.host = host
        self.port = port
        self.threads = threads

    def run(self):
        """
        Run waitress server.
        """
        serve(
            self.app,
            host=self.host,
            port=self.port,
            threads=self.threads,
            connection_limit=1000,
            channel_timeout=30,
            asyncore_loop_timeout=1,
            _quiet=True
        )


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.

    :return: arguments dictionary
    """
    parser = argparse.ArgumentParser(
        description='DRUI (Docker Registry UI)',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument('-c',
                        '--config',
                        help='path to the configuration file',
                        action='store',
                        type=str,
                        dest='config')

    parser.add_argument('-d',
                        '--dev',
                        help='start at development mode',
                        action='store_true',
                        dest='dev_mode',
                        default=False)

    parser.add_argument('-v',
                        '--version',
                        action='version',
                        version=f'drui {__version__}')

    return parser.parse_args()


def load_configuration(config_path: str) -> None:
    """
    Load configuration from the specified path.

    :param config_path: path to the configuration file 
    :return:
    """
    if config_path and not CONF.read(config_path):
        print(f'ERROR: cannot read configuration file: {abspath(config_path)}', file=sys.stderr)
        sys.exit(2)


def print_startup_info(config_path: str, host: str, port: int, registry_endpoint: str) -> None:
    """
    Print startup information.

    :param config_path: path to the configuration file
    :param host: host for listening
    :param port: port for listening
    :param registry_endpoint: registry endpoint
    :return:
    """
    print(
        f'* Starting DRUI ({__version__})\n'
        f'* Configuration file: {config_path}\n'
        f'* Listen address: {host}:{port}\n'
        f'* Registry endpoint: {registry_endpoint}\n'
    )


def run_application(server: Flask, host: str, port: int, dev_mode: bool) -> None:
    """
    Run the application in either development or production mode.

    :param server:
    :param host: host for listening
    :param port: port for listening
    :param dev_mode: start at development mode
    :return:
    """
    try:
        if dev_mode:
            server.run(host=host, port=port, debug=True, threaded=True)
        else:
            WSGIApplication(server, host=host, port=port).run()
    except Exception as error:
        print(f'ERROR: {error}', file=sys.stderr)
        sys.exit(2)


def main() -> None:
    """
    Main function to start the Registry UI application.
    """
    args = parse_arguments()
    load_configuration(args.config)

    host = CONF.get('host', default='0.0.0.0')
    port = CONF.getint('port', default=8000)
    registry_endpoint = CONF.get('endpoint', 'registry')

    # start metrics worker
    if CONF.getboolean('enable', section='metrics') and not environ.get('WERKZEUG_RUN_MAIN'):
        exit_function = getattr(util, '_exit_function')
        atexit.unregister(exit_function)

        worker = Process(target=metrics.run, kwargs={'conf': CONF})
        worker.start()

    # start DRUI
    print_startup_info(args.config, host, port, registry_endpoint)
    server = init_app(CONF)
    run_application(server, host, port, args.dev_mode)


if __name__ == '__main__':
    sys.exit(main())
