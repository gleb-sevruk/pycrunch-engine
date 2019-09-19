import subprocess
import sys
import os
from multiprocessing.connection import Listener, Client
from pprint import pprint
from threading import Thread

from pycrunch.introspection.history import execution_history
from pycrunch.session import config

import logging

logger = logging.getLogger(__name__)

class MultiprocessTestRunner:

    def __init__(self, timeout, timeline):
        self.timeline = timeline
        self.timeout = timeout
        self.results = None

    def results_did_become_available(self, results):
        logger.debug('results avail:')
        logger.debug(results)
        self.results = results

    def run(self, tests):
        # todo should be dynamic??
        address = ('localhost', 6001)  # family is deduced to be 'AF_INET'
        listener = Listener(address, authkey=b'secret password')

        # data = '{"tests":[{"fqn":"pycrunch.tests.test_modules_cleanup:test_nested","module":"pycrunch.tests.test_modules_cleanup","filename":"/Users/gleb/code/PyCrunch/pycrunch/tests/test_modules_cleanup.py","name":"test_nested","state":"pending"}]}'
        # socket.setdefaulttimeout(60)
        def thread_loop(params=None):
            self.timeline.mark_event('Entered TCP thread')
            logger.debug('Waiting for connection')
            conn = listener.accept()
            logger.debug(f'connection accepted from {listener.last_accepted}')
            self.timeline.mark_event('TCP: Accepted connection')
            conn.send(tests)
            self.timeline.mark_event('TCP: Sent tests to be run...')
            while True:
                poll_result = conn.poll(timeout=1)
                msg = conn.recv()
                # do something with msg
                if msg == 'close':
                    logger.debug('close TCP client...')
                    conn.close()
                    break
                else:
                    logger.debug('got msg from client:')
                    # pprint(msg)
                    if msg.kind == 'test_run_results':
                        results = msg.data_to_send
                        self.timeline.mark_event('TCP: Got test run results from subprocess')
                        self.results_did_become_available(results)
                    if msg.kind == 'timings':
                        self.timeline.mark_event('TCP: Got timings from subprocess')
                        execution_history.save(msg.data_to_send)


            listener.close()
        self.timeline.mark_event('Creating tcp thread')
        t = Thread(target=thread_loop)
        t.daemon = True
        t.start()
        engine_root = f' {config.engine_directory}{os.sep}pycrunch{os.sep}multiprocess_child_main.py '
        hardcoded_path = engine_root + f'--engine={config.runtime_engine}'
        self.timeline.mark_event('Subprocess: starting...')

        try:
            proc = subprocess.check_call(sys.executable + hardcoded_path, cwd=config.working_directory, shell=True)
        except Exception as e:
            logger.error('Exception in subprocess, need restart :(' + str(e))
            self.timeline.mark_event('Subprocess: exception during test run.')
            address = ('localhost', 6001)
            conn = Client(address, authkey=b'secret password')
            conn.send('close')
            # self.results = dict()

        self.timeline.mark_event('Subprocess: completed.')
        # isAlive() after join() to decide whether a timeout happened -- if the
        #         thread is still alive, the join() call timed out.
        t.join(self.timeout)
        logger.debug(f'thread completed: isAlive: {t.isAlive()}')