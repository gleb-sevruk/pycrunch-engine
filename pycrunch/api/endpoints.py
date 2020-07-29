
import io
from pathlib import Path

# from flask import jsonify, Response
# from flask_socketio import send

from pycrunch import runner
from pycrunch.api.shared import file_watcher
from pycrunch.discovery.simple import SimpleTestDiscovery
from pycrunch.pipeline import execution_pipeline
from pycrunch.pipeline.run_test_task import RunTestTask
from pycrunch.session import config
from pycrunch.session.state import engine
from pycrunch.shared.models import all_tests

import logging

logger = logging.getLogger(__name__)


# @pycrunch_api.route("/")
# def hello():
#     return "Nothing here"


# @pycrunch_api.route("/discover")
# def discover_tests():
#     engine.will_start_test_discovery()
#     return jsonify(dict(ack=True))

#
# @pycrunch_api.route("/diagnostics")
# def queue_diagnostics():
#     engine.will_start_diagnostics_collection()
#     return jsonify(dict(ack=True))


# @pycrunch_api.route("/timings")
# def queue_timings():
#     engine.will_send_timings()
#     return jsonify(dict(ack=True))


# @pycrunch_api.route("/pin-tests", methods=['POST'])
# def pin_tests():
#     # fqns = array of strings[]
#     fqns = request.json.get('fqns')
#     engine.tests_will_pin(fqns)
#     return jsonify(dict(ack=True))


# @pycrunch_api.route("/engine-mode", methods=['POST'])
# def engine_mode():
#     new_mode = request.json.get('mode')
#     engine.engine_mode_will_change(new_mode)
#     return jsonify(dict(ack=True))

# @pycrunch_api.route("/unpin-tests", methods=['POST'])
# def unpin_tests():
#     # fqns = array of strings[]
#     fqns = request.json.get('fqns')
#     engine.tests_will_unpin(fqns)
#     return jsonify(dict(ack=True))
#
# @pycrunch_api.route("/run-tests", methods=['POST'])
# def run_tests():
#
#     tests = request.json.get('tests')
#     logger.info('Running tests...')
#     logger.info(tests)
#     fqns = set()
#     for test in tests:
#         fqns.add(test['fqn'])
#
#     tests_to_run = all_tests.collect_by_fqn(fqns)
#
#     execution_pipeline.add_task(RunTestTask(tests_to_run))
#     return jsonify(tests)



# @pycrunch_api.route("/file", methods=['GET'])
# def download_file():
#     filename = request.args.get('file')
#     logger.debug('download_file ' + filename)
#     target_file = config.path_mapping.map_local_to_remote(filename)
#     my_file = io.FileIO(target_file, 'r')
#     content = my_file.read()
#     return Response(content, mimetype='application/x-python-code')

