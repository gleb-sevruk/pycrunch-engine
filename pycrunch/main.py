import logging.config
from pathlib import Path

import yaml
from flask import Flask
from flask_cors import CORS

from pycrunch.api import shared
from pycrunch.api import pycrunch_api

app = Flask(__name__)

shared.socketio.init_app(app=app)
parent = Path(__file__).parent
print(parent)
configuration_yaml_ = parent.joinpath('log_configuration.yaml')
print(configuration_yaml_)

with open(configuration_yaml_, 'r') as f:
    logging.config.dictConfig(yaml.safe_load(f.read()))

CORS(app)
app.config['SECRET_KEY'] = '!pycrunch!'


app.register_blueprint(pycrunch_api)

import pycrunch.api.socket_handlers


def run():
    use_reloader = not True
    shared.socketio.run(app, use_reloader=use_reloader, debug=True, extra_files=['log_configuration.yaml'])


if __name__ == '__main__':
    run()
