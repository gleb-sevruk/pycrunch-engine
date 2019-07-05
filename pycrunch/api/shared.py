from pprint import pprint
from time import perf_counter

from flask_socketio import SocketIO
from pycrunch.watcher.fs_watcher import FSWatcher

file_watcher = FSWatcher()
socketio = SocketIO()
timestamp = perf_counter

class ExternalPipe:
    def push(self, event_type, **kwargs):
        # pprint(kwargs)
        socketio.emit('event',
                             dict(
                                 event_type=event_type,
                                 **kwargs
                             ),
                             namespace='/')


pipe = ExternalPipe()