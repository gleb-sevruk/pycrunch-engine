from asyncio import Queue

import logging

from pycrunch.watchdog.tasks import AbstractWatchdogTask

logger = logging.getLogger(__name__)





class WatchdogPipeline:
    def __init__(self):
        self.q = Queue()

    def add_task(self, task: AbstractWatchdogTask):
        logger.debug('Received task in queue')
        self.q.put_nowait(task)

    async def get_task(self):
        return await self.q.get()


watchdog_pipeline = WatchdogPipeline()
