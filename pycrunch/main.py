

import logging.config
import os
from pathlib import Path

import aiohttp
import yaml
from aiohttp import web

from pycrunch.session import config


parent = Path(__file__).parent
print(parent)
config.set_engine_directory(parent.parent)
configuration_yaml_ = parent.joinpath('log_configuration.yaml')
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

    async def root_handler(request):
        return aiohttp.web.HTTPFound('/ui/index.html')

    app.router.add_route('*', '/ui/', root_handler)
    app.add_routes([web.static('/ui', 'front/dist')])
    app.add_routes([web.static('/js', 'front/dist/js')])
    app.add_routes([web.static('/css', 'front/dist/css')])

    web.run_app(app, port=port, host='0.0.0.0')
    # app.listen(port=port, address='0.0.0.0')
    # tornado.ioloop.IOLoop.current().start()


    # sio.run(app, debug=True)
    # import eventlet

    # eventlet.wsgi.server(eventlet.listen(('', port)),  app,)

    # shared.socketio.run(app, use_reloader=use_reloader, debug=True, extra_files=['log_configuration.yaml'], host='0.0.0.0', port=port)


if __name__ == '__main__':
    run()
