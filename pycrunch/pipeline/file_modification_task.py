import time

from pycrunch.api import shared
from pycrunch.pipeline import execution_pipeline
from pycrunch.pipeline.abstract_task import AbstractTask
from pycrunch.pipeline.run_test_task import RunTestTask
from pycrunch.session.combined_coverage import combined_coverage


class FileModifiedNotificationTask(AbstractTask):
    def __init__(self, file):
        self.file = file
        self.timestamp = time.time()

    def run(self):
        shared.pipe.push(event_type='file_modification',
                         modified_file=self.file,
                         ts=self.timestamp,
                         )

        dependencies = combined_coverage.dependencies
        if dependencies:
            tests = dependencies[self.file]
            execution_pipeline.add_task(RunTestTask(tests))

        pass;

# https://stackoverflow.com/questions/45369128/python-multithreading-queue
