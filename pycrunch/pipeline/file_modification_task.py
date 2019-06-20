import time

from pycrunch.api import shared
from pycrunch.pipeline.abstract_task import AbstractTask


class FileModifiedNotificationTask(AbstractTask):
    def __init__(self, file):
        self.file = file
        self.timestamp = time.time()

    def run(self):
        shared.pipe.push(event_type='file_modification',
                         modified_file=self.file,
                         ts=self.timestamp,
                         )

        pass;

# https://stackoverflow.com/questions/45369128/python-multithreading-queue
