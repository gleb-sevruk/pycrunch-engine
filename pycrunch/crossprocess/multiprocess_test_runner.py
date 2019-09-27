import asyncio
import sys
import os
from pycrunch.scheduling.scheduler import TestRunScheduler
from pycrunch.scheduling.server_protocol import TestRunnerServerProtocol
from pycrunch.session import config

import logging

logger = logging.getLogger(__name__)

class MultiprocessTestRunner:

    def __init__(self, timeout, timeline):
        self.client_connections = []
        self.completion_futures = []
        self.timeline = timeline
        self.timeout = timeout
        self.results = None

    def results_did_become_available(self, results):
        logger.debug('results avail:')
        logger.debug(results)
        self.results = results

    async def run(self, tests):
        self.timeline.mark_event(f'Splitting into CPU tasks. Total tests to run: {len(tests)}')
        #
        self.tasks = TestRunScheduler(cpu_cores=config.cpu_cores, threshold=config.multiprocessing_threshold).schedule_into_tasks(tests)
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
            child_processes.append(asyncio.create_subprocess_shell(self.get_command_line_for_child(port,task.id), cwd=config.working_directory, shell=True))

        logger.debug(f'Waiting for startup of {len(self.tasks)} subprocess task(s)')
        # wait to start all
        subprocesses_results = await asyncio.gather(*child_processes)
        logger.debug('Startup complete')

        child_waiters = []
        for coro in subprocesses_results:
            child_waiters.append(coro.wait())

        logger.debug('Begin waiting for subprocess completion...')
        # await asyncio.wait_for(asyncio.gather(*child_waiters), 5)
        await asyncio.gather(*child_waiters)
        logger.debug('All subprocesses are completed')

        logger.debug(f'Waiting for completion from TCP server')
        demo_results = await asyncio.gather(*self.completion_futures)
        logger.debug(f'TCP ran to the end')
        self.results = self.merge_task_results(demo_results)
        server.close()

        logger.debug(f'TCP server and child processes ran to the end')

    def get_command_line_for_child(self, port, task_id):
        engine_root = f' {config.engine_directory}{os.sep}pycrunch{os.sep}multiprocess_child_main.py '
        hardcoded_path = engine_root + f'--engine={config.runtime_engine} --port={port} --task-id={task_id}'
        return sys.executable + hardcoded_path

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