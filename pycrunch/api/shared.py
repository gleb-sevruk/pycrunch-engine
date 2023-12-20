from asyncio import shield

import socketio

from pycrunch.watcher.fs_watcher import FSWatcher

file_watcher = FSWatcher()


# async_mode='threading'
# async_mode='tornado'
# async_mode='eventlet'
async_mode = 'aiohttp'

# log_ws_internals = True
log_ws_internals = False
sio_instance = None


def sio():
    global sio_instance
    if sio_instance is None:
        sio_instance = socketio.AsyncServer(
            async_mode=async_mode,
            cors_allowed_origins='*',
            logger=log_ws_internals,
            engineio_logger=log_ws_internals,
        )
    return sio_instance


class ExternalPipe:
    async def push(self, event_type, **kwargs):
        # print(f'ws event: {event_type}')
        # pprint(kwargs)

        await shield(
            sio().emit('event', dict(event_type=event_type, **kwargs), namespace='/')
        )


pipe = ExternalPipe()
