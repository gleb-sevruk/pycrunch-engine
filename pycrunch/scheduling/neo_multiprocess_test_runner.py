import asyncio
import subprocess
import sys
import os
from multiprocessing.connection import Listener, Client
from pprint import pprint
from threading import Thread

from pycrunch.introspection.history import execution_history
from pycrunch.scheduling.concurrent_multiprocess_run import EchoServerProtocol
from pycrunch.scheduling.scheduler import TestRunScheduler
from pycrunch.session import config

import logging

logger = logging.getLogger(__name__)

class NeoMultiprocessTestRunner:

    def __init__(self, timeout, timeline):
        self.timeline = timeline
        self.timeout = timeout
        self.results = None

    def results_did_become_available(self, results):
        logger.debug('results avail:')
        logger.debug(results)
        self.results = results

    async def run(self, tests):
        self.tasks = TestRunScheduler(cpu_cores=4).schedule_into_tasks(tests)
        # todo should be dynamic??
        port = 6001
        address = ('localhost', port)  # family is deduced to be 'AF_INET'
        # listener = Listener(address, authkey=b'secret password')

        # data = '{"tests":[{"fqn":"pycrunch.tests.test_modules_cleanup:test_nested","module":"pycrunch.tests.test_modules_cleanup","filename":"/Users/gleb/code/PyCrunch/pycrunch/tests/test_modules_cleanup.py","name":"test_nested","state":"pending"}]}'
        # socket.setdefaulttimeout(60)
        # def thread_loop(params=None):
        #     self.timeline.mark_event('Entered TCP thread')
        #     logger.debug('Waiting for connection')
        #     conn = listener.accept()
        #     logger.debug(f'connection accepted from {listener.last_accepted}')
        #     self.timeline.mark_event('TCP: Accepted connection')
        #     conn.send(tests)
        #     self.timeline.mark_event('TCP: Sent tests to be run...')
        #     while True:
        #         poll_result = conn.poll(timeout=1)
        #         msg = conn.recv()
        #         # do something with msg
        #         if msg == 'close':
        #             logger.debug('close TCP client...')
        #             conn.close()
        #             break
        #         else:
        #             logger.debug('got msg from client:')
        #             # pprint(msg)
        #             if msg.kind == 'test_run_results':
        #                 results = msg.data_to_send
        #                 self.timeline.mark_event('TCP: Got test run results from subprocess')
        #                 self.results_did_become_available(results)
        #             if msg.kind == 'timings':
        #                 self.timeline.mark_event('TCP: Got timings from subprocess')
        #                 execution_history.save(msg.data_to_send)
        #     listener.close()

        self.timeline.mark_event('Creating tcp thread')

        loop = asyncio.get_event_loop()
        server = await loop.create_server(
            lambda: self.create_server_protocol(),
            '127.0.0.1', port)

        engine_root = f' {config.engine_directory}{os.sep}pycrunch{os.sep}neo_multiprocess_child_main.py '
        hardcoded_path = engine_root + f'--engine={config.runtime_engine} --port={port} --task-id={self.tasks[0].id}'
        self.timeline.mark_event('Subprocess: starting...')

        def run_in_thread():
            try:
                proc = subprocess.check_call(sys.executable + hardcoded_path, cwd=config.working_directory, shell=True)
            except Exception as e:
                logger.error('Exception in subprocess, need restart :(' + str(e))
                self.timeline.mark_event('Subprocess: exception during test run.')
                # todo close connection
                # address = ('localhost', port)
                # conn = Client(address, authkey=b'secret password')
                # conn.send('close')
                # self.results = dict()


        t = Thread(target=run_in_thread)
        t.daemon = True
        t.start()

        self.timeline.mark_event('Subprocess: completed.')
        # isAlive() after join() to decide whether a timeout happened -- if the
        #         thread is still alive, the join() call timed out.
        logger.debug(f'tcp server completed')
        print('before await')
        await asyncio.sleep(2.1)
        # await asyncio.wait(self.client_futures)
        server.close()
        print(' await self.completion_future')
        self.results = await self.completion_future
        print('after await')


    def create_server_protocol(self):
        loop = asyncio.get_event_loop()
        self.completion_future = loop.create_future()
        # self.client_futures.append(completion_future)
        return EchoServerProtocol(self.tasks, self.completion_future, self.timeline)