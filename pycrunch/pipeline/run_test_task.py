import subprocess
import sys
from datetime import datetime
from multiprocessing.connection import Listener
from pprint import pprint
from queue import Queue
import time
from threading import Thread

from pycrunch import session
from pycrunch.api import shared
from pycrunch.api.serializers import serialize_test_run
from pycrunch.api.shared import file_watcher
from pycrunch.crossprocess.multiprocess_test_runner import MultiprocessTestRunner
from pycrunch.pipeline.abstract_task import AbstractTask
from pycrunch.plugins.django_support.django_runner_engine import DjangoRunnerEngine
from pycrunch.plugins.pytest_support.cleanup_contextmanager import ModuleCleanup
from pycrunch.plugins.pytest_support.pytest_runner_engine import  PyTestRunnerEngine
from pycrunch.plugins.simple.simple_runner_engine import SimpleTestRunnerEngine
from pycrunch.runner.test_runner import TestRunner
from pycrunch.session import config
from pycrunch.session.combined_coverage import combined_coverage, CombinedCoverage
from pycrunch.session.state import engine


def serialize_combined_coverage(combined: CombinedCoverage):
    return [
        dict(
            filename=x.filename,
            lines_with_entrypoints=compute_lines(x)) for x in combined.files.values()
    ]


def compute_lines(x):
    zzz = {line_number:list(entry_points) for (line_number, entry_points) in x.lines_with_entrypoints.items()}
    return zzz

    # return result


class RunTestTask(AbstractTask):

    def __init__(self, tests):
        self.timestamp = shared.timestamp()
        self.tests = tests
        self.results = None

    def results_available(self, results):
        print('results avail:')
        pprint(results)
        self.results = results

    def run(self):
        runner_engine = None
        if session.config.runtime_engine == 'simple':
            runner_engine = SimpleTestRunnerEngine()
        elif session.config.runtime_engine == 'pytest':
            runner_engine = PyTestRunnerEngine()
        elif session.config.runtime_engine == 'django':
            runner_engine = DjangoRunnerEngine()

        engine.tests_will_run(self.tests)

        runner = MultiprocessTestRunner(30)
        runner.run(tests=self.tests)
        self.results = runner.results
        # runner = TestRunner(runner_engine=runner_engine)
        # with ModuleCleanup() as cleanup:
        #     results = runner.run(self.tests)
        if self.results is not None:
            print('results are not none')
        if self.results is None:
            print('!!! None in results')

        engine.tests_did_run(self.results)

        combined_coverage.add_multiple_results(self.results)

        results_as_json = dict()
        for k,v in self.results.items():
            results_as_json[k] = v.as_json()


        shared.pipe.push(event_type='test_run_completed',
                         coverage=dict(all_runs=results_as_json),
                         data=self.tests,
                         timings=dict(start=self.timestamp, end=shared.timestamp()),
                         ),

        serialized = serialize_combined_coverage(combined_coverage)
        shared.pipe.push(event_type='combined_coverage_updated',
                         combined_coverage=serialized,
                         dependencies={entry_point: list(filenames) for entry_point, filenames in combined_coverage.dependencies.items() },
                         timings=dict(start=self.timestamp, end=shared.timestamp()),
                         ),
        pass;

# https://stackoverflow.com/questions/45369128/python-multithreading-queue
