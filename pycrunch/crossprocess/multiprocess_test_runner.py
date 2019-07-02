import subprocess
import sys
from multiprocessing.connection import Listener
from pprint import pprint
from threading import Thread

from pycrunch.session import config


class MultiprocessTestRunner:

    def __init__(self, timeout):
        self.timeout = timeout
        self.results = None

    def results_did_become_available(self, results):
        print('results avail:')
        pprint(results)
        self.results = results

    def run(self, tests):
        address = ('localhost', 6001)  # family is deduced to be 'AF_INET'
        listener = Listener(address, authkey=b'secret password')

        # data = '{"tests":[{"fqn":"pycrunch.tests.test_modules_cleanup:test_nested","module":"pycrunch.tests.test_modules_cleanup","filename":"/Users/gleb/code/PyCrunch/pycrunch/tests/test_modules_cleanup.py","name":"test_nested","state":"pending"}]}'

        def thread_loop(params=None):
            print('Waiting for connection')
            conn = listener.accept()
            print('connection accepted from', listener.last_accepted)
            conn.send(tests)
            while True:
                poll_result = conn.poll(timeout=1)
                msg = conn.recv()
                # do something with msg
                if msg == 'close':
                    print('close TCP client...')
                    conn.close()
                    break
                else:
                    print('got msg from client:')
                    pprint(msg)
                    results = msg
                    self.results_did_become_available(results)

            listener.close()

        t = Thread(target=thread_loop)
        t.daemon = True
        t.start()
        hardcoded_path = ' /Users/gleb/code/PyCrunch/multiprocess_child_main.py'
        proc = subprocess.check_call(sys.executable + hardcoded_path, cwd=config.working_directory, shell=True)
        pprint(proc)
        # isAlive() after join() to decide whether a timeout happened -- if the
        #         thread is still alive, the join() call timed out.
        t.join(self.timeout)
        print(f'thread completed: {t.isAlive()}')