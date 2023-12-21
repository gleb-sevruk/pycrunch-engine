# Event handler for the 'my_response' event
from time import sleep

from pycrunch.insights import trace


def my_response_handler(data):
    trace(data)

def test_x():
    import socketio

    # Create a Socket.IO client
    sio = socketio.Client()

    # Define the connection URL
    url = "http://127.0.0.1:10100"

    sio.on('event', my_response_handler)
    # Connect to the WebSocket
    sio.connect(url, transports='websocket')

    # Now do your magic here. Send messages, handle responses, etc.
    sio.emit('my event', {'action': 'discovery'})
    sleep(1)
    # Don't forget to disconnect when you're done
    sio.disconnect()
    pass

