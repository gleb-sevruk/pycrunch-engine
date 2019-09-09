import logging.config
from pathlib import Path

import yaml
from flask import Flask
from flask_cors import CORS

from pycrunch.api import shared
from pycrunch.api.endpoints import pycrunch_api
from pycrunch.session import config

app = Flask(__name__)

shared.socketio.init_app(app=app)
parent = Path(__file__).parent
print(parent)
config.set_engine_directory(parent.parent)
configuration_yaml_ = parent.joinpath('log_configuration.yaml')
print(configuration_yaml_)
with open(configuration_yaml_, 'r') as f:
    logging.config.dictConfig(yaml.safe_load(f.read()))


CORS(app)
app.config['SECRET_KEY'] = '!pycrunch!'


app.register_blueprint(pycrunch_api)

import pycrunch.api.socket_handlers


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
    shared.socketio.run(app, use_reloader=use_reloader, debug=True, extra_files=['log_configuration.yaml'], host='0.0.0.0', port=port)


if __name__ == '__main__':
    run()
