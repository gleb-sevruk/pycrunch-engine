from datetime import datetime
from queue import Queue
import time

from pycrunch.api import shared
from pycrunch.pipeline.abstract_task import AbstractTask


class FileModificationTask(AbstractTask):
    def __init__(self, file):
        self.file = file
        self.timestamp = time.time()

    def run(self):
        # shared.socketio.emit('event',
        #                      dict(
        #                          type='pipeline_task',
        #                          # data=task.file,
        #                          ts=self.timestamp,
        #                      ),
        #                      namespace='/')
        pass;

# https://stackoverflow.com/questions/45369128/python-multithreading-queue
