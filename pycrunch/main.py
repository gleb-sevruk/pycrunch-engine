import asyncio
import logging.config
from pathlib import Path
import yaml
from aiohttp import web

from pycrunch import web_ui
from pycrunch.session import config
from pycrunch.session.state import engine
from pycrunch.watchdog.connection_watchdog import connection_watchdog

package_directory = Path(__file__).parent
print(package_directory)
engine_directory = package_directory.parent
config.set_engine_directory(engine_directory)
configuration_yaml_ = package_directory.joinpath('log_configuration.yaml')
print(configuration_yaml_)
with open(configuration_yaml_, 'r') as f:
    logging.config.dictConfig(yaml.safe_load(f.read()))




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
    use_reloader = not True


    from pycrunch.api import shared
    from pycrunch.api.socket_handlers import attach_message_handlers_to_sio
    engine.prepare_runtime_configuration_if_necessary()

    app = web.Application()

    sio = shared.sio()

    attach_message_handlers_to_sio(sio)
    sio.attach(app)

    if config.enable_web_ui:
        # This will enable PyCrunch web interface
        print(f'PyCrunch Web-UI at http://0.0.0.0:{port}/ui/')
        print(f'                or http://127.0.0.1:{port}/ui/')
        web_ui.enable_for_aiohttp(app, package_directory)
    else:
        print(f'PyCrunch Web-UI is disabled.')




    loop = asyncio.get_event_loop()
    task = loop.create_task(connection_watchdog.watch_client_connection_loop())
    loop.set_debug(config.enable_asyncio_debug)
    web.run_app(app, port=port, host='0.0.0.0', shutdown_timeout=1)


    # eventlet.wsgi.server(eventlet.listen(('', port)),  app,)

    # shared.socketio.run(app, use_reloader=use_reloader, debug=True, extra_files=['log_configuration.yaml'], host='0.0.0.0', port=port)


if __name__ == '__main__':
    run()
