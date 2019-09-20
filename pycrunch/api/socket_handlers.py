import asyncio
import io
import logging
import threading
import uuid

# from flask import url_for, session, current_app, request
# from flask_socketio import emit, send

from pycrunch.api.shared import pipe
from pycrunch.pipeline import execution_pipeline
from pycrunch.pipeline.download_file_task import DownloadFileTask
from pycrunch.pipeline.run_test_task import RunTestTask
from pycrunch.runner.pipeline_dispatcher import dispather_thread
from pycrunch.session import config
from pycrunch.session.state import engine
from pycrunch.shared.models import all_tests
from . import shared

logger = logging.getLogger(__name__)

@shared.sio.on('message')
def handle_message(message):
    logger.debug('received message 2: ' + message)




@shared.sio.on('json')
def handle_json(json):
    logger.debug('handle_json')
    # logger.debug(session['userid'])
    # url_for1 = url_for('my event', _external=True)
    # logger.debug('url + ' + url_for1)
    pipe.push(event_type='connected', **{'data': 'Connected'})
    logger.debug('received json 2: ' + str(json))

@shared.sio.on('my event')
async def handle_my_custom_event(sid, json):
    logger.debug('received json (my event 2): ' + str(json))
    if 'action' not in json:
        logger.debug('no action specified')

    action = json.get('action')
    if action == 'discovery':
        await engine.will_start_test_discovery()
    if action == 'run-tests':
        if 'tests' not in json:
            logger.error('run-tests command received, but no tests specified')
            return
        logger.info('Running tests...')
        tests = json.get('tests')
        fqns = set()
        for test in tests:
            fqns.add(test['fqn'])

        tests_to_run = all_tests.collect_by_fqn(fqns)

        execution_pipeline.add_task(RunTestTask(tests_to_run))
    if action == 'load-file':
        filename = json.get('filename')
        logger.debug('download_file ' + filename)
        #         return asynchronously
        execution_pipeline.add_task(DownloadFileTask(filename))
    if action == 'diagnostics':
        await engine.will_start_diagnostics_collection()
    if action == 'timings':
        await engine.will_send_timings()
    if action == 'pin-tests':
        # fqns = array of strings[]
        fqns = json.get('fqns')
        await engine.tests_will_pin(fqns)
    if action == 'unpin-tests':
        fqns = json.get('fqns')
        await engine.tests_will_unpin(fqns)
    if action == 'engine-mode':
        new_mode = json.get('mode')
        engine.engine_mode_will_change(new_mode)

from threading import Lock
thread_lock = Lock()
thread = None

@shared.sio.event
async def connect(sid, environ):
    global thread
    logger.debug('Client test_connected')

    await pipe.push(event_type='connected', **{'data': 'Connected test_connected' })
    with thread_lock:
        if thread is None:
            # thread = shared.socketio.start_background_task(target=dispather_thread, arg=42)
            # pass
            # thread = thread.start_new_thread(dispather_thread, args=42)
            thread = 1
            loop = asyncio.get_event_loop()
            loop.create_task(dispather_thread())
            # thread = threading.Thread(target=dispather_thread)
            # thread.start()
            # thread.run()

@shared.sio.event
def disconnect(sid):
    logger.debug('Client disconnected')