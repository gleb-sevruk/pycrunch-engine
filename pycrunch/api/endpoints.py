
import io

from flask import jsonify, Response
from flask_socketio import send

from pycrunch import runner
from pycrunch.api.shared import file_watcher
from pycrunch.discovery.simple import SimpleTestDiscovery
from pycrunch.pipeline import execution_pipeline
from pycrunch.pipeline.run_test_task import RunTestTask
from pycrunch.session.state import engine
from .serializers import serialize_test_run
from flask import Blueprint
from flask import request

import logging

logger = logging.getLogger(__name__)

pycrunch_api = Blueprint('pycrunch_api', __name__)

@pycrunch_api.route("/")
def hello():
    return "Nothing here"

def get_files():
 return [
     '/Users/gleb/code/PyCrunch/tests.py',
     '/Users/gleb/code/PyCrunch/playground.py',
 ]

@pycrunch_api.route("/entry-files")
def entry_file():
    return jsonify(dict(entry_files=get_files()))


@pycrunch_api.route("/discover")
def discover_tests():
    folder = request.args.get('folder')
    engine.will_start_test_discovery(folder=folder)


    return jsonify(dict(ack=True))


@pycrunch_api.route("/run-tests", methods=['POST'])
def run_tests():

    tests = request.json.get('tests')
    execution_pipeline.add_task(RunTestTask(tests))
    return jsonify(tests)



@pycrunch_api.route("/file", methods=['GET'])
def download_file():
    filename = request.args.get('file')
    logger.debug('download_file ' + filename)
    my_file = io.FileIO(filename, 'r')
    content = my_file.read()
    return Response(content, mimetype='application/x-python-code')

