from asyncio import Queue

import logging

logger = logging.getLogger(__name__)


class ExecutionPipeline:
    def __init__(self):
        self.q = Queue()

    def add_task(self, task: "AbstractTask"):
        logger.debug('Received task in queue')
        self.q.put_nowait(task)

    async def get_task(self):
        return await self.q.get()

    def put_raw(self, abstract_task):
        self.q.put(abstract_task)

execution_pipeline = ExecutionPipeline()
