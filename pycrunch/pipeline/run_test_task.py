from pprint import pprint

from pycrunch import session
from pycrunch.api import shared
from pycrunch.crossprocess.multiprocess_test_runner import MultiprocessTestRunner
from pycrunch.introspection.history import execution_history
from pycrunch.introspection.timings import Timeline
from pycrunch.pipeline.abstract_task import AbstractTask
from pycrunch.plugins.django_support.django_runner_engine import DjangoRunnerEngine
from pycrunch.plugins.pytest_support.pytest_runner_engine import  PyTestRunnerEngine
from pycrunch.plugins.simple.simple_runner_engine import SimpleTestRunnerEngine
from pycrunch.session.combined_coverage import combined_coverage, serialize_combined_coverage
from pycrunch.session.state import engine

import logging

logger = logging.getLogger(__name__)

class RunTestTask(AbstractTask):

    def __init__(self, tests):
        self.timestamp = shared.timestamp()
        self.tests = tests
        self.results = None
        self.timeline = Timeline('run tests')
        self.timeline.start()

    def results_available(self, results):
        print('results avail:')
        pprint(results)
        self.results = results

    async def run(self):
        self.timeline.mark_event('run')
        runner_engine = None
        if session.config.runtime_engine == 'simple':
            runner_engine = SimpleTestRunnerEngine()
        elif session.config.runtime_engine == 'pytest':
            runner_engine = PyTestRunnerEngine()
        elif session.config.runtime_engine == 'django':
            runner_engine = DjangoRunnerEngine()

        await engine.tests_will_run(self.tests)
        converted_tests = list()
        for test in self.tests:
            converted_tests.append(dict(fqn=test.discovered_test.fqn, filename=test.discovered_test.filename,name=test.discovered_test.name, module=test.discovered_test.module, state='converted'))

        runner = MultiprocessTestRunner(30, self.timeline)
        self.timeline.mark_event('before running tests')
        runner.run(tests=converted_tests)
        self.results = runner.results
        # runner = TestRunner(runner_engine=runner_engine)
        # with ModuleCleanup() as cleanup:
        #     results = runner.run(self.tests)
        if self.results is not None:
            logger.debug('results are not none')
        if self.results is None:
            logger.error('!!! None in results')

        self.timeline.mark_event('before tests_did_run')
        if not self.results:
            self.results = dict()

        await engine.tests_did_run(self.results)

        self.timeline.mark_event('Postprocessing: combined coverage, line hits, dependency tree')
        combined_coverage.add_multiple_results(self.results)
        self.timeline.mark_event('Postprocessing: completed')


        results_as_json = dict()
        for k,v in self.results.items():
            results_as_json[k] = v.as_json()

        self.timeline.mark_event('Sending: test_run_completed event')

        await shared.pipe.push(event_type='test_run_completed',
                         coverage=dict(all_runs=results_as_json),
                         # data=serialize_test_set_state(self.tests),
                         timings=dict(start=self.timestamp, end=shared.timestamp()),
                         ),

        self.timeline.mark_event('Started combined coverage serialization')
        serialized = serialize_combined_coverage(combined_coverage)
        self.timeline.mark_event('Completed combined coverage serialization')

        self.timeline.mark_event('Send: combined coverage over WS')
        await shared.pipe.push(event_type='combined_coverage_updated',
                         combined_coverage=serialized,
                         dependencies={entry_point: list(filenames) for entry_point, filenames in combined_coverage.dependencies.items() },
                         aggregated_results=engine.all_tests.legacy_aggregated_statuses(),
                         timings=dict(start=self.timestamp, end=shared.timestamp()),
                         ),

        self.timeline.mark_event('Send: done, stopping timeline')

        self.timeline.stop()
        execution_history.save(self.timeline)

        pass;


# https://stackoverflow.com/questions/45369128/python-multithreading-queue
