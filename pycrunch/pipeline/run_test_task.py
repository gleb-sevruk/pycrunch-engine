import asyncio
from pprint import pprint

from pycrunch.api import shared
from pycrunch.crossprocess.multiprocess_test_runner import MultiprocessTestRunner
from pycrunch.introspection.history import execution_history
from pycrunch.introspection.timings import Timeline
from pycrunch.pipeline.abstract_task import AbstractTask
from pycrunch.scheduling.scheduler import TestRunScheduler
from pycrunch.session.combined_coverage import combined_coverage, serialize_combined_coverage
from pycrunch.session.state import engine
from pycrunch.session import config

import logging

logger = logging.getLogger(__name__)


class RunTestTask(AbstractTask):
    def __init__(self, tests):
        self.timestamp = shared.timestamp()
        self.tests = tests
        self.results = None
        self.timeline = Timeline('run tests')
        self.timeline.start()

    async def run(self):
        """
            Here we run multiple tests at once using one or multiple processes
        """
        self.timeline.mark_event('run')
        async_tasks = [
            # notify status over websocket
            engine.tests_will_run(self.tests)
        ]

        converted_tests = self.get_converted_test_list()
        runner = self.create_test_runner()

        self.timeline.mark_event('before running tests')

        async_tasks.append(runner.run(tests=converted_tests))
        task_results = await asyncio.gather(*async_tasks)

        run_results = task_results[-1]

        if run_results is not None:
            logger.debug('results are not none')
        if run_results is None:
            logger.error('!!! None in results')
            run_results = dict()

        self.timeline.mark_event('before tests_did_run')

        # asynchronously send message over websocket
        async_tasks_post = [
            engine.tests_did_run(run_results)
        ]

        self.post_process_combined_coverage(run_results)

        self.timeline.mark_event('Sending: test_run_completed event')
        # todo: i'm only using `filename` in connector, why bother with everything?
        cov_to_send = dict(all_runs=self.convert_result_to_json(run_results))
        async_tasks_post.append(shared.pipe.push(
            event_type='test_run_completed',
            coverage=cov_to_send,
            timings=dict(start=self.timestamp, end=shared.timestamp()),
        ))

        self.timeline.mark_event('Started combined coverage serialization')
        serialized = serialize_combined_coverage(combined_coverage)
        self.timeline.mark_event('Completed combined coverage serialization')

        self.timeline.mark_event('Sending: combined coverage over WS')
        async_tasks_post.append(
            shared.pipe.push(
                event_type='combined_coverage_updated',
                combined_coverage=serialized,
                # Todo: why do I need dependencies to be exposed? It is internal state.
                # dependencies=self.build_dependencies(),
                # todo what is that?
                aggregated_results=engine.all_tests.legacy_aggregated_statuses(),
                timings=dict(start=self.timestamp, end=shared.timestamp()),
            ))

        self.timeline.mark_event('Waiting until post-processing tasks are completed')
        await asyncio.gather(*async_tasks_post)

        self.timeline.mark_event('Send: done, stopping timeline')

        self.timeline.stop()
        execution_history.save(self.timeline)

    def convert_result_to_json(self, run_results):
        results_as_json = dict()
        for k, v in run_results.items():
            results_as_json[k] = v.as_json()
        return results_as_json

    def post_process_combined_coverage(self, run_results):
        self.timeline.mark_event('Postprocessing: combined coverage, line hits, dependency tree')
        combined_coverage.add_multiple_results(run_results)
        self.timeline.mark_event('Postprocessing: completed')

    def create_test_runner(self):
        runner = MultiprocessTestRunner(
            timeout=30,
            timeline=self.timeline,
            test_run_scheduler=TestRunScheduler(
                cpu_cores=config.cpu_cores,
                threshold=config.multiprocessing_threshold
            )
        )
        return runner

    def build_dependencies(self):
        return {entry_point: list(filenames) for entry_point, filenames in combined_coverage.dependencies.items()}

    def get_converted_test_list(self):
        converted_tests = list()
        for test in self.tests:
            # todo why is this line exist?
            converted_tests.append(
                dict(fqn=test.discovered_test.fqn, filename=test.discovered_test.filename, name=test.discovered_test.name, module=test.discovered_test.module, state='converted'))
        return converted_tests

# https://stackoverflow.com/questions/45369128/python-multithreading-queue
