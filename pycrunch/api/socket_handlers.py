import logging
import threading
import uuid

from flask import url_for, session, current_app, request
from flask_socketio import emit, send

from pycrunch.api.shared import pipe
from pycrunch.runner.pipeline_dispatcher import dispather_thread
from . import shared

logger = logging.getLogger(__name__)

@shared.socketio.on('message')
def handle_message(message):
    logger.debug('received message 2: ' + message)




@shared.socketio.on('json')
def handle_json(json):
    logger.debug('handle_json')
    logger.debug(session['userid'])
    # url_for1 = url_for('my event', _external=True)
    # logger.debug('url + ' + url_for1)
    pipe.push(event_type='connected', **{'data': 'Connected'})
    logger.debug('received json 2: ' + str(json))

@shared.socketio.on('my event')
def handle_my_custom_event(json):
    logger.debug('received json (my event 2): ' + str(json))


from threading import Lock
thread_lock = Lock()
thread = None

@shared.socketio.on('connect')
def test_connect():
    global thread
    logger.debug('Client test_connected')

    pipe.push(event_type='connected', **{'data': 'Connected test_connected' })
    with thread_lock:
        if thread is None:
            thread = shared.socketio.start_background_task(target=dispather_thread, arg=42)

@shared.socketio.on('disconnect')
def test_disconnect():
    logger.debug('Client disconnected')