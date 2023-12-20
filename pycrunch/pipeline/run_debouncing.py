import asyncio
import logging
import sys
import typing
from asyncio import get_event_loop, sleep
from typing import List

from pycrunch.introspection.clock import clock
from pycrunch.pipeline import execution_pipeline
from pycrunch.pipeline.run_test_task import RemoteDebugParams, RunTestTask

if typing.TYPE_CHECKING:
    from pycrunch.shared.models import TestState

logger = logging.getLogger(__name__)


class RunDebouncer:
    def __init__(self, debounce_delay: 'float'):
        self.run_timer = None  # type: 'function'
        now = clock.now()
        self.ts_created = now
        self.ts_target = now + debounce_delay
        self.ts_target = None
        self.run_pending = False
        self.dirty_tests = []
        self.debounce_delay = debounce_delay
        self._loop = get_event_loop()

    def reset_deadline(self, multiplier=1.0):
        now = clock.now()
        self.ts_created = now
        delay_multiplier = self.debounce_delay * multiplier
        if delay_multiplier > 0.85:
            delay_multiplier = 0.85
        self.ts_target = now + delay_multiplier  # (s)

    def delay_a_little(self):
        now = clock.now()
        inside_debounce_interval = self.ts_created < now < self.ts_target
        # print(f' {self.ts_created} < {now} < {self.ts_target}')
        # print(f' === {inside_debounce_interval}')
        if inside_debounce_interval:
            self.ts_target += self.debounce_delay * 1

            if self.ts_target - now > 1.0:
                self.ts_target = 1.0
            if self.ts_target - now < 0:
                self.ts_target = 0.05

            logger.debug(
                f' delay_a_little: updated ts_target, to run in {round(self.ts_target - now, 4)} secs'
            )

            if self.run_pending and self.run_timer:
                logger.debug('run_pending, cancelling...')
                copied_ref = self.run_timer
                copied_ref.cancel()
                logger.debug(
                    ' Cancelled pending run. Waiting for more tests to run at once.'
                )
                self.run_timer = None
                self.force_schedule_run()

    def add_tests(self, tests: "List[TestState]"):
        # until we have tests, wait...
        logger.info(f'add_tests: {len(tests)} ')
        if len(self.dirty_tests) <= 0:
            self.reset_deadline(execution_pipeline.tasks_in_queue())
        if len(self.dirty_tests) > 0:
            # we have something in queue, lets wait even more.
            # if there is nothing in queue - intention to run it immediately without waiting
            self.delay_a_little()
        self.dirty_tests.extend(tests)
        logger.debug('2: ran to the end')

    async def schedule_run(self):
        if self.run_pending:
            logger.debug('run_pending already. skip')
            return

        self.run_pending = True
        self.force_schedule_run()

    def force_schedule_run(self):
        self.run_timer = self._loop.create_task(self.execute_with_delay())

    async def execute_with_delay(self):
        target_at_enter = self.ts_target
        try:
            delay = target_at_enter - clock.now()
            if delay < self.debounce_delay:
                delay = self.debounce_delay
            logger.debug(f'execute_with_delay->waiting for {round(delay, 4)} seconds')
            while clock.now() < target_at_enter:
                await self.sleep_for_mutiple_python_versions()
        except asyncio.CancelledError:
            logger.debug('execute_with_delay: cancelled to aggregate more tasks')
            return
        except Exception as e:
            logger.exception('exc', exc_info=e)
            return

        # after sleep, it may not be a good idea to cancel; use events?
        copy_of_list = list(self.dirty_tests)
        logger.info(
            f'execute_with_delay: Total {len(copy_of_list)} tests will run with delay {round(delay, 4)} seconds',
        )

        execution_pipeline.add_task(
            # While this is running - append only, do not issue another tasks
            RunTestTask(copy_of_list, RemoteDebugParams.disabled())
        )
        self.dirty_tests = []
        self.run_pending = False
        self.reset_deadline()
        self.run_timer = None

    async def sleep_for_mutiple_python_versions(self):
        if sys.version_info >= (3, 10):
            await sleep(0.01)
        else:
            await sleep(0.01, loop=self._loop)
