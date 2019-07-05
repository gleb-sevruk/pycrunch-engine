import multiprocessing
import subprocess
import sys
from pprint import pprint
from threading import Thread


def nottest_single_multiprocess():
    from multiprocessing.connection import Listener
    address = ('localhost', 6002)  # family is deduced to be 'AF_INET'
    listener = Listener(address, authkey=b'secret password')
    data = '{"tests":[{"fqn":"pycrunch.tests.test_modules_cleanup:test_nested","module":"pycrunch.tests.test_modules_cleanup","filename":"/Users/gleb/code/PyCrunch/pycrunch/tests/test_modules_cleanup.py","name":"test_nested","state":"pending"}]}'

    def thread_loop(params=None):
        print('Waiting for connection')
        conn = listener.accept()
        print('connection accepted from', listener.last_accepted)
        conn.send(data)
        while True:
            msg = conn.recv()
            # do something with msg
            if msg == 'close':
                conn.close()
                break
            else:
                print('got msg from client:')
                pprint(msg)

        listener.close()
    t = Thread(target=thread_loop)
    t.daemon = True
    t.start()
    proc = subprocess.check_call(sys.executable +' /Users/gleb/code/PyCrunch/multiprocess_child_main.py', cwd='/Users/gleb/code/PyCrunch', shell=True)
    pprint(proc)
    t.join(50)
    print('Timeout exceed')

