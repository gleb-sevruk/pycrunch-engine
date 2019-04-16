import logging

from pycrunch.api import shared
from pycrunch.watcher.pipeline import execution_pipeline

logger = logging.getLogger(__name__)

def dispather_thread(arg):
    logger.debug('OPA THGREAD!')
    count = 1
    while True:
        task = execution_pipeline.get_task()

        shared.socketio.emit('event',
                             dict(
                                 type='pipeline_task',
                                 data=task.file,
                                 ts=task.timestamp,
                             ),
                             namespace='/')

        count += 1

    logger.debug('OPA THGREAD --- done!')