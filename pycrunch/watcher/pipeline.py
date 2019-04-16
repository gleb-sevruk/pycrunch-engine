from datetime import datetime
from queue import Queue
import time


class PipelineTask:
    def __init__(self, file):
        self.file = file
        self.timestamp = time.time()

# https://stackoverflow.com/questions/45369128/python-multithreading-queue
class ExecutionPipeline:
    def __init__(self):
        self.q = Queue()

    def add_file(self, file):
        self.q.put(PipelineTask(file=file))

    def get_task(self):
        return self.q.get(block=True)

execution_pipeline = ExecutionPipeline()