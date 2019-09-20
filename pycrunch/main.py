import asyncio
import logging.config
import os
from pathlib import Path

import aiohttp
import yaml
from aiohttp import web

from pycrunch import web_ui
from pycrunch.session import config


package_directory = Path(__file__).parent
print(package_directory)
engine_directory = package_directory.parent
config.set_engine_directory(engine_directory)
configuration_yaml_ = package_directory.joinpath('log_configuration.yaml')
print(configuration_yaml_)
with open(configuration_yaml_, 'r') as f:
    logging.config.dictConfig(yaml.safe_load(f.read()))




import socketio



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
    use_reloader = not True

    from pycrunch.api.shared import sio
    from pycrunch.api import shared
    import pycrunch.api.socket_handlers

    # sio = socketio.Server()


    # settings = {
    #     "static_path": os.path.join(os.path.dirname(__file__), "front/dist"),
    #
    # }

    # _Handler = socketio.get_tornado_handler(sio)
    #
    # class SocketHandler(_Handler):
    #     def check_origin(self, origin):
    #         return True
    #
    #
    # app = tornado.web.Application(
    #     [
    #         (r'/ui/(.*)', tornado.web.StaticFileHandler, {"path" : 'front/dist'}),
    #         (r'/js/(.*)', tornado.web.StaticFileHandler, {"path" : 'front/dist/js'}),
    #         (r'/css/(.*)', tornado.web.StaticFileHandler, {"path" : 'front/dist/css'}),
    #         (r"/socket.io/", SocketHandler),
    #     ],
    #     # **settings
    #     # ... other application options
    # )
    app = web.Application()

    sio.attach(app)
    # This will enable PyCrunch web interface
    web_ui.enable_for_aiohttp(app, package_directory)

    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    web.run_app(app, port=port, host='0.0.0.0')
    # app.listen(port=port, address='0.0.0.0')
    # tornado.ioloop.IOLoop.current().start()


    # sio.run(app, debug=True)
    # import eventlet

    # eventlet.wsgi.server(eventlet.listen(('', port)),  app,)

    # shared.socketio.run(app, use_reloader=use_reloader, debug=True, extra_files=['log_configuration.yaml'], host='0.0.0.0', port=port)


if __name__ == '__main__':
    run()
