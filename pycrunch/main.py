import asyncio
import logging.config
import sys
from pathlib import Path

import yaml
from aiohttp import web

import pycrunch.version
from pycrunch.execution_watchdog.connection_watchdog import connection_watchdog
from pycrunch.session import config

package_directory = Path(__file__).parent
print(package_directory)
engine_directory = package_directory.parent
config.set_engine_directory(engine_directory)
configuration_yaml_ = package_directory.joinpath('log_configuration.yaml')
print(configuration_yaml_)
with open(configuration_yaml_, 'r') as f:
    logging.config.dictConfig(yaml.safe_load(f.read()))


if sys.platform == 'win32':
    policy = asyncio.get_event_loop_policy()
    policy._loop_factory = asyncio.ProactorEventLoop


def run():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, help="Port number to listen")
    args = parser.parse_args()
    port = 5000
    if args.port:
        port = args.port
    print(f'PyCrunch [v{pycrunch.version.version_info_str}]; port will be {port} ')
    # use_reloader = not True
    from pycrunch.session.state import engine

    engine.prepare_runtime_configuration_if_necessary()

    from pycrunch.api import shared
    from pycrunch.api.socket_handlers import attach_message_handlers_to_sio

    app = web.Application()

    sio = shared.sio()

    attach_message_handlers_to_sio(sio)
    sio.attach(app)

    if config.enable_web_ui:
        # This will enable PyCrunch web interface
        print(f'PyCrunch Web-UI at http://0.0.0.0:{port}/ui/')
        print(f'                or http://127.0.0.1:{port}/ui/')
        print('')
        print('Files in watch:')
        print(f'                or http://127.0.0.1:{port}/watched-files/')
        from . import web_ui

        web_ui.enable_for_aiohttp(app, package_directory)
    else:
        print('PyCrunch Web-UI is disabled. ')
        print(
            '    To enable it back, please set `engine->enable-web-ui` in `.pycrunch-config.yaml` to true'
        )

    loop = asyncio.get_event_loop()
    loop.create_task(connection_watchdog.watch_client_connection_loop())
    loop.set_debug(config.enable_asyncio_debug)

    from pycrunch.compatibility.aiohttp_shim import aiohttp_init_parameters

    additional_kw = aiohttp_init_parameters()

    web.run_app(app, port=port, host='0.0.0.0', shutdown_timeout=1, **additional_kw)


if __name__ == '__main__':
    run()
