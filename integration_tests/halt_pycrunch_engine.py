from time import sleep

import socketio

from pycrunch_integration_tests.pycrunch_engine_int_test import (
    PYCRUNCH_API_URL,
    EVENT_NAME,
    Actions,
)


def create_connection():
    client = socketio.Client()
    client.connect(PYCRUNCH_API_URL, transports='websocket')
    return client


if __name__ == '__main__':
    print("Running halt_pycrunch_engine.py at address " + PYCRUNCH_API_URL)
    sio = create_connection()
    print("sending {'action': 'halt'}...")

    sio.emit(EVENT_NAME, Actions.halt())
    sleep(2)
    sio.disconnect()
