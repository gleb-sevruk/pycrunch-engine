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
from pycrunch.api.serializers import serialize_test_run, serialize_test_set_state
from pycrunch.crossprocess.multiprocess_test_runner import MultiprocessTestRunner
from pycrunch.pipeline.abstract_task import AbstractTask
from pycrunch.plugins.django_support.django_runner_engine import DjangoRunnerEngine
from pycrunch.plugins.pytest_support.cleanup_contextmanager import ModuleCleanup
from pycrunch.plugins.pytest_support.pytest_runner_engine import  PyTestRunnerEngine
from pycrunch.plugins.simple.simple_runner_engine import SimpleTestRunnerEngine
from pycrunch.session import config
from pycrunch.session.combined_coverage import combined_coverage, CombinedCoverage, serialize_combined_coverage
from pycrunch.session.state import engine
from pycrunch.shared import TestMetadata


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
        converted_tests = list()
        for test in self.tests:
            converted_tests.append(dict(fqn=test.discovered_test.fqn, filename=test.discovered_test.filename,name=test.discovered_test.name, module=test.discovered_test.module, state='converted'))

        runner = MultiprocessTestRunner(30)
        runner.run(tests=converted_tests)
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
                         # data=serialize_test_set_state(self.tests),
                         timings=dict(start=self.timestamp, end=shared.timestamp()),
                         ),

        serialized = serialize_combined_coverage(combined_coverage)
        shared.pipe.push(event_type='combined_coverage_updated',
                         combined_coverage=serialized,
                         dependencies={entry_point: list(filenames) for entry_point, filenames in combined_coverage.dependencies.items() },
                         aggregated_results=engine.all_tests.legacy_aggregated_statuses(),
                         timings=dict(start=self.timestamp, end=shared.timestamp()),
                         ),
        pass;


# https://stackoverflow.com/questions/45369128/python-multithreading-queue
