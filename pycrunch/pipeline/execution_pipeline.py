from asyncio import Queue

from pycrunch.pipeline.abstract_task import AbstractTask
import logging

logger = logging.getLogger(__name__)


class ExecutionPipeline:
    def __init__(self):
        self.q = Queue()

    def add_task(self, task):
        logger.debug('Received task in queue')
        self.q.put_nowait(task)

    async def get_task(self):
        return await self.q.get()


execution_pipeline = ExecutionPipeline()