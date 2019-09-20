from asyncio import shield
from pprint import pprint
from time import perf_counter

import socketio
from pycrunch.watcher.fs_watcher import FSWatcher

file_watcher = FSWatcher()
# async_mode='threading'
# async_mode='tornado'
# async_mode='eventlet'
async_mode='aiohttp'

# log_ws_internals = True
log_ws_internals = False
sio = socketio.AsyncServer(async_mode=async_mode, cors_allowed_origins='*', logger=log_ws_internals, engineio_logger=log_ws_internals)
timestamp = perf_counter

class ExternalPipe:
    async def push(self, event_type, **kwargs):
        # pprint(kwargs)
        await shield(sio.emit('event',
                       dict(
                           event_type=event_type,
                           **kwargs
                       ),
                       namespace='/'))


pipe = ExternalPipe()