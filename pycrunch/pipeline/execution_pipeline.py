from queue import Queue

from pycrunch.pipeline.abstract_task import AbstractTask


class ExecutionPipeline:
    def __init__(self):
        self.q = Queue()

    def add_task(self, task):
        self.q.put(task)

    def get_task(self) -> AbstractTask:
        return self.q.get(block=True)


execution_pipeline = ExecutionPipeline()