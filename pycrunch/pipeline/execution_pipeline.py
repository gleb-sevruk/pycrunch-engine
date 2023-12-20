import logging
import typing
from asyncio import Queue

if typing.TYPE_CHECKING:
    from pycrunch.pipeline.abstract_task import AbstractTask

logger = logging.getLogger(__name__)


class ExecutionPipeline:
    def __init__(self):
        self.q = Queue()

    def add_task(self, task: "AbstractTask"):
        logger.debug('Received task in queue')
        self.q.put_nowait(task)

    def tasks_in_queue(self):
        return self.q.qsize()

    async def get_task(self):
        return await self.q.get()

    async def put_raw(self, abstract_task):
        await self.q.put(abstract_task)


execution_pipeline = ExecutionPipeline()
