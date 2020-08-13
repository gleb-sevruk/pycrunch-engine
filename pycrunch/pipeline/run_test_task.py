import asyncio
import os
from typing import Dict, Any, Optional

from pycrunch.api import shared
from pycrunch.api.serializers import CoverageRun
from pycrunch.crossprocess.multiprocess_test_runner import MultiprocessTestRunner
from pycrunch.introspection.clock import clock
from pycrunch.introspection.history import execution_history
from pycrunch.introspection.timings import Timeline
from pycrunch.pipeline.abstract_task import AbstractTask
from pycrunch.runner.execution_result import ExecutionResult
from pycrunch.scheduling.scheduler import TestRunScheduler
from pycrunch.session.combined_coverage import combined_coverage, serialize_combined_coverage
from pycrunch.session.state import engine
from pycrunch.session import config

import logging

from pycrunch.watchdog.tasks import TestExecutionBeginTask, TestExecutionEndTask
from pycrunch.watchdog.watchdog import termination_event
from pycrunch.watchdog.watchdog_pipeline import watchdog_pipeline

logger = logging.getLogger(__name__)


class TestRunStatus:
    def __init__(self, status, results = None):
        """
        :type state: str
        :type results: Dict[str, CoverageRun]
        """
        if results is not None:
            logger.debug('results are not none')
        if results is None:
            logger.error('!!! None in results')
            results = dict()
        self.status = status
        self.results = results

    def is_failed(self):
        return self.status != 'success'


class RemoteDebugParams:
    def __init__(self, enabled: bool, port: Optional[int] = None):
        self.port = port
        self.enabled = enabled

    @classmethod
    def disabled(cls):
        return RemoteDebugParams(False)

class RunTestTask(AbstractTask):
    def __init__(self, tests, remote_debug_params: RemoteDebugParams):
        self.remote_debug_params = remote_debug_params
        self.timestamp = clock.now()
        self.tests = tests
        self.results = None
        self.timeline = Timeline('run tests')
        self.timeline.start()

    async def run(self):
        """
            Here we run multiple tests at once using one or multiple processes
        """
        self.timeline.mark_event('run')
        watchdog_pipeline.add_task(TestExecutionBeginTask(len(self.tests)))
        socket_notification_task = asyncio.ensure_future(engine.tests_will_run(self.tests))

        converted_tests = self.get_converted_test_list()
        runner = self.create_test_runner()

        # while not cancelled
        runner_task = asyncio.ensure_future(runner.run(tests=converted_tests))
        run_results_compound = await self.wait_with_cancellation(runner_task)
        if run_results_compound.is_failed():
            failure_reason = self.user_friendly_error_message(run_results_compound.status)

            for _ in converted_tests:
                candidate_fqn = _['fqn']
                cov_run = CoverageRun(candidate_fqn, -1, None, execution_result=ExecutionResult.create_failed_with_reason(failure_reason))
                run_results_compound.results[candidate_fqn] = cov_run


        run_results = run_results_compound.results

        self.timeline.mark_event('before tests_did_run')

        # asynchronously send message over websocket
        # Line bellow communicates test statuses as a side effect
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
            timings=dict(start=self.timestamp, end=clock.now()),
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
                aggregated_results=engine.all_tests.legacy_aggregated_statuses(),
                timings=dict(start=self.timestamp, end=clock.now()),
            ))

        self.timeline.mark_event('Waiting until post-processing tasks are completed')
        await asyncio.gather(*async_tasks_post)
        watchdog_pipeline.add_task(TestExecutionEndTask())

        self.timeline.mark_event('Send: done, stopping timeline')

        self.timeline.stop()
        execution_history.save(self.timeline)

    def user_friendly_error_message(self, status: str):
        failure_reason = 'epic fail'
        if status == 'terminated':
            failure_reason = 'Test execution terminated by user.'
        if status == 'timeout':
            line1 = f'Timeout of {config.execution_timeout_in_seconds} seconds reached while waiting for test execution to complete.'
            line2 = f'Consider increasing it in .pycrunch-config.yaml, e.g.:'
            line3 = f'{os.linesep}engine:{os.linesep}    timeout: 999{os.linesep}'
            line4 = f'Setting it to zero will wait forever.{os.linesep}'
            line5 = 'https://pycrunch.com/docs/configuration-file'
            failure_reason = os.linesep.join([line1, line2, line3, line4, line5])
        return failure_reason

    def convert_result_to_json(self, run_results):
        results_as_json = dict()
        for k, v in run_results.items():
            results_as_json[k] = v.as_json()
        return results_as_json

    def post_process_combined_coverage(self, run_results):
        if self.remote_debug_params.enabled:
            self.timeline.mark_event('Postprocessing: combined coverage will not be recomputed.')
            return

        self.timeline.mark_event('Postprocessing: combined coverage, line hits, dependency tree')
        combined_coverage.add_multiple_results(run_results)
        self.timeline.mark_event('Postprocessing: completed')

    def create_test_runner(self):
        self.timeline.mark_event('before running tests')

        runner = MultiprocessTestRunner(
            timeout=config.get_execution_timeout(),
            timeline=self.timeline,
            test_run_scheduler=TestRunScheduler(
                cpu_cores=config.cpu_cores,
                threshold=config.multiprocessing_threshold
            ),
            remote_debug_params=self.remote_debug_params,
        )
        return runner

    async def wait_with_cancellation(self, runner_task: asyncio.Future) -> TestRunStatus:
        try:
            # Here we wait for the first event, which may be:
            # 1. Watchdog termination signal
            # 2. Test runner events
            #  2.1 Run to end
            #  2.2 Timeout during run
            waited = await asyncio.wait([termination_event.wait(), runner_task], return_when=asyncio.FIRST_COMPLETED)
            if runner_task.done():
                return TestRunStatus('success', runner_task.result())
            if termination_event.is_set():
                logger.warning('Looks like task was cancelled by user...')
                runner_task.cancel()
                return TestRunStatus('terminated')
        except asyncio.TimeoutError:
            logger.warning('Timeout reached while waiting for tests...')
            return TestRunStatus('timeout')


    def get_converted_test_list(self):
        converted_tests = list()
        for test in self.tests:
            # todo why is this line exist?
            converted_tests.append(
                dict(fqn=test.discovered_test.fqn, filename=test.discovered_test.filename, name=test.discovered_test.name, module=test.discovered_test.module, state='converted'))
        return converted_tests

# https://stackoverflow.com/questions/45369128/python-multithreading-queue
