import asyncio
import logging

from pycrunch.api.shared import pipe
from pycrunch.watchdog.tasks import AbstractWatchdogTask, TestExecutionBeginTask, TestExecutionEndTask
from pycrunch.watchdog.watchdog_pipeline import watchdog_pipeline

logger = logging.getLogger(__name__)

# Block until the internal flag is true.
termination_event = asyncio.Event()

class WatchdogDispatcher:
    def __init__(self):
        pass

    async def run_once(self):
        task = await watchdog_pipeline.get_task()
        await self.execute_task(task)

    async def execute_task(self, task: AbstractWatchdogTask):
        if task.name == 'watchdog_begin':
            task: TestExecutionBeginTask = task
            termination_event.clear()
            await pipe.push(
                event_type='watchdog_begin',
                total_tests=task.total_tests
            )
        if task.name == 'watchdog_end':
            task: TestExecutionEndTask = task
            termination_event.clear()
            await pipe.push(
                event_type='watchdog_end',
            )
        if task.name == 'watchdog_terminate':
            termination_event.set()


async def watchdog_dispather_thread():
    logger.info('WatchDog Dispatcher thread -- Start')
    dp = WatchdogDispatcher()

    while True:
        logger.debug('WatchDog Dispatcher thread -- inside event loop, waiting for task...')
        try:
            await dp.run_once()
        except asyncio.CancelledError:
            logger.warning('CancelledError while processing WatchDog Dispatcher queue')
            break
        except Exception as e:
            logger.exception('Exception in WatchDog Dispatcher Thread, ', exc_info=e)
            break

    logger.debug('WatchDog Dispatcher thread -- End')
