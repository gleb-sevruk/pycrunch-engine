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
from pycrunch.pipeline.run_test_task import RunTestTask, RemoteDebugParams
from pycrunch.runner.pipeline_dispatcher import dispather_thread
from pycrunch.session import config
from pycrunch.session.state import engine
from pycrunch.shared.models import all_tests
from . import shared
from .. import version
from ..watchdog.connection_watchdog import connection_watchdog
from ..watchdog.tasks import TerminateTestExecutionTask
from ..watchdog.watchdog import watchdog_dispather_thread
from ..watchdog.watchdog_pipeline import watchdog_pipeline

logger = logging.getLogger(__name__)

@shared.sio.on('message')
def handle_message(message):
    logger.debug('received message 2: ' + message)




@shared.sio.on('json')
async def handle_json(json, smth):
    logger.debug('handle_json')
    # logger.debug(session['userid'])
    # url_for1 = url_for('my event', _external=True)
    # logger.debug('url + ' + url_for1)
    await pipe.push(event_type='connected', **{'data': 'Connected'})
    logger.debug('received json 2: ' + str(json))





@shared.sio.on('my event')
async def handle_my_custom_event(sid, json):
    logger.debug('received json (my event 2): ' + str(json))
    if 'action' not in json:
        logger.debug('no action specified')

    action = json.get('action')
    if action == 'discovery':
        await engine.will_start_test_discovery()
    if action == 'run-tests' or action == 'debug-tests':
        if 'tests' not in json:
            logger.error('run-tests command received, but no tests specified')
            return
        logger.info('Running tests...')
        tests = json.get('tests')
        fqns = set()
        for test in tests:
            fqns.add(test['fqn'])

        tests_to_run = all_tests.collect_by_fqn(fqns)
        if action == 'debug-tests':
            debugger_port = json.get('debugger_port')
            debug_params = RemoteDebugParams(True, debugger_port)
        else:
            debug_params = RemoteDebugParams.disabled()

        execution_pipeline.add_task(RunTestTask(tests_to_run, debug_params))
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
    if action == 'watchdog-terminate':
        print('action == watchdog-terminate -> TerminateTestExecutionTask')
        watchdog_pipeline.add_task(TerminateTestExecutionTask())


from threading import Lock
thread_lock = Lock()
thread = None
watchdog_thread = None

@shared.sio.event
async def connect(sid, environ):
    global thread
    global watchdog_thread
    logger.debug('Client test_connected')
    connection_watchdog.connection_established()
    await pipe.push(
        event_type='connected',
        **dict(
            data='Connected test_connected',
            engine_mode=engine.get_engine_mode(),
            version=version.version_info
        )
    )
    with thread_lock:
        if thread is None:
            thread = 1
            loop = asyncio.get_event_loop()
            loop.create_task(dispather_thread())

        if watchdog_thread is None:
            watchdog_thread = 1
            loop = asyncio.get_event_loop()
            loop.create_task(watchdog_dispather_thread())

@shared.sio.event
def disconnect(sid):
    logger.debug('Client disconnected')
    connection_watchdog.connection_lost()
