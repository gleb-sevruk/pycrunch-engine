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
from pycrunch.crossprocess.multiprocess_test_runner import MultiprocessTestRunner
from pycrunch.pipeline.abstract_task import AbstractTask
from pycrunch.plugins.django_support.django_runner_engine import DjangoRunnerEngine
from pycrunch.plugins.pytest_support.cleanup_contextmanager import ModuleCleanup
from pycrunch.plugins.pytest_support.pytest_runner_engine import  PyTestRunnerEngine
from pycrunch.plugins.simple.simple_runner_engine import SimpleTestRunnerEngine
from pycrunch.session import config
from pycrunch.session.combined_coverage import combined_coverage, CombinedCoverage, serialize_combined_coverage
from pycrunch.session.state import engine



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
                         aggregated_results={fqn: dict(test_run_short_info) for fqn, test_run_short_info in combined_coverage.aggregated_results.items()},
                         timings=dict(start=self.timestamp, end=shared.timestamp()),
                         ),
        pass;

# https://stackoverflow.com/questions/45369128/python-multithreading-queue
