import asyncio
import sys
import os
from typing import List, Optional

from pycrunch.networking.server_protocol import TestRunnerServerProtocol

import logging

from pycrunch.session import config

logger = logging.getLogger(__name__)

class MultiprocessTestRunner:

    def __init__(self, timeout: Optional[float], timeline, test_run_scheduler, remote_debug_params: "RemoteDebugParams"):
        self.client_connections: List[TestRunnerServerProtocol] = []
        self.completion_futures = []
        self.timeline = timeline
        self.timeout = timeout
        self.results = None
        self.test_run_scheduler = test_run_scheduler
        self.remote_debug_params = remote_debug_params

    def results_did_become_available(self, results):
        logger.debug('results avail:')
        logger.debug(results)
        self.results = results

    async def run(self, tests):
        self.timeline.mark_event(f'Splitting into CPU tasks. Total tests to run: {len(tests)}')
        #

        self.tasks = self.test_run_scheduler.schedule_into_tasks(tests)
        self.timeline.mark_event('Creating tcp thread')

        loop = asyncio.get_event_loop()
        server = await loop.create_server(
            lambda: self.create_server_protocol(),
            '127.0.0.1')
        # Allocate dynamic port. Extract port number from socket.
        port = server.sockets[0].getsockname()[1]
        self.timeline.mark_event('Subprocess: starting...')

        logger.debug('Initializing subprocess...')
        child_processes = []
        for task in self.tasks:
            child_processes.append(self.create_child_subprocess(port, task))

        logger.debug(f'Waiting for startup of {len(self.tasks)} subprocess task(s)')
        subprocesses_results = await asyncio.gather(*child_processes)
        logger.debug('Startup complete')

        child_waiters = []
        for _ in subprocesses_results:
            child_waiters.append(_.wait())

        logger.debug('Begin waiting for subprocess completion...')
        timeout_reached = False
        try:
            await asyncio.wait_for(
                asyncio.gather(*child_waiters),
                timeout=self.timeout_if_non_debug()
            )
        except (asyncio.TimeoutError, asyncio.CancelledError) as e:
            timeout_reached = True
            logger.warning(f'Reached execution timeout of {self.timeout_if_non_debug()} seconds. ')
            for _ in subprocesses_results:
                try:
                    _.kill()
                except:
                    logger.warning('Cannot kill child runner process with, ignoring.')

        logger.debug('All subprocesses are completed')
        logger.debug(f'Waiting for completion from TCP server')
        demo_results = []
        try:
            demo_results = await asyncio.wait_for(
                asyncio.gather(*self.completion_futures, return_exceptions=True),
                timeout=self.timeout_if_non_debug()
            )
        except asyncio.TimeoutError as ex:
            print(ex)
            for _ in self.client_connections:
                _.force_close()
            for _ in child_processes:
                _.close()
                print(_)
            pass

        logger.debug(f'TCP ran to the end')
        logger.debug(f'1 - merge_task_results')
        _results = self.merge_task_results(demo_results)
        logger.debug(f'1 - done')

        server.close()

        logger.debug(f' ---- TCP server and child processes ran to the end')
        if timeout_reached:
            raise asyncio.TimeoutError('Test execution timeout.')
        return _results

    def create_child_subprocess(self, port, task):
        # sys.executable is a full path to python.exe (or ./python) in current virtual environment
        return asyncio.create_subprocess_exec(sys.executable, *self.get_command_line_for_child(port, task.id), cwd=config.working_directory)

    def timeout_if_non_debug(self) -> Optional[float]:
        if self.remote_debug_params.enabled:
            return None
        return self.timeout

    def get_command_line_for_child(self, port, task_id):
        results = []
        results.append(f'{config.engine_directory}{os.sep}pycrunch{os.sep}multiprocess_child_main.py')
        results.append(f'--engine={config.runtime_engine}')
        results.append(f'--port={port}')
        results.append(f'--task-id={task_id}')
        results.append(f'--load-pytest-plugins={str(config.load_pytest_plugins).lower()}')
        if self.remote_debug_params.enabled:
            results.append(f'--enable-remote-debug')
            results.append(f'--remote-debugger-port={self.remote_debug_params.port}')
        return results

    def create_server_protocol(self):
        loop = asyncio.get_event_loop()
        completion_future = loop.create_future()
        self.completion_futures.append(completion_future)

        # self.client_futures.append(completion_future)
        protocol = TestRunnerServerProtocol(self.tasks, completion_future, self.timeline)
        self.client_connections.append(protocol) 
        return protocol

    def merge_task_results(self, demo_results):
        self.timeline.mark_event('merging task results')
        new_dict = dict()
        # here are multiple dictionaries coming from each subprocess:
        for results_by_fqn in demo_results:
            new_dict.update(results_by_fqn)

        self.timeline.mark_event('merging task results -- Completed')
        self.timeline.mark_event(f'Total results processed {len(new_dict)}')

        return new_dict