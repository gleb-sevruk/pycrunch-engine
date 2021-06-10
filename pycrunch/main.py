import asyncio
import logging.config
import os
from pathlib import Path

import aiohttp
import yaml
from aiohttp import web

from pycrunch import web_ui
from pycrunch.session import config
from pycrunch.watchdog.connection_watchdog import connection_watchdog

package_directory = Path(__file__).parent
print(package_directory)
engine_directory = package_directory.parent
config.set_engine_directory(engine_directory)
configuration_yaml_ = package_directory.joinpath('log_configuration.yaml')
print(configuration_yaml_)
with open(configuration_yaml_, 'r') as f:
    logging.config.dictConfig(yaml.safe_load(f.read()))




import socketio
import sys

if sys.platform == 'win32':
    policy = asyncio.get_event_loop_policy()
    policy._loop_factory = asyncio.ProactorEventLoop


def run():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int,
                        help="Port number to listen")
    args = parser.parse_args()
    port = 5000
    if args.port:
        port = args.port
    print(f'PyCrunch port will be {port}')
    print(f'PyCrunch Web-UI at http://0.0.0.0:{port}/ui/')
    print(f'                or http://127.0.0.1:{port}/ui/')
    use_reloader = not True

    from pycrunch.api.shared import sio
    from pycrunch.api import shared
    import pycrunch.api.socket_handlers

    app = web.Application()

    sio.attach(app)
    # This will enable PyCrunch web interface
    web_ui.enable_for_aiohttp(app, package_directory)



    loop = asyncio.get_event_loop()
    task = loop.create_task(connection_watchdog.watch_client_connection_loop())
    loop.set_debug(True)
    web.run_app(app, port=port, host='0.0.0.0', shutdown_timeout=3)
    # app.listen(port=port, address='0.0.0.0')
    # tornado.ioloop.IOLoop.current().start()


    # sio.run(app, debug=True)
    # import eventlet

    # eventlet.wsgi.server(eventlet.listen(('', port)),  app,)

    # shared.socketio.run(app, use_reloader=use_reloader, debug=True, extra_files=['log_configuration.yaml'], host='0.0.0.0', port=port)


if __name__ == '__main__':
    run()
