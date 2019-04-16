import logging.config
import yaml
from flask import Flask
from flask_cors import CORS

from pycrunch.api import shared
from pycrunch.api import pycrunch_api

app = Flask(__name__)

shared.socketio.init_app(app=app)

with open('log_configuration.yaml', 'r') as f:
    config = yaml.safe_load(f.read())
    logging.config.dictConfig(config)

CORS(app)
app.config['SECRET_KEY'] = '!pycrunch!'


app.register_blueprint(pycrunch_api)

import pycrunch.api.socket_handlers

if __name__ == '__main__':

    shared.socketio.run(app, use_reloader=False, debug=True, extra_files=['log_configuration.yaml'])
