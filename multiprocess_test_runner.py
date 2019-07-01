import argparse
import json
import multiprocessing
import os
import sys
from pathlib import Path
from pprint import pprint
from time import sleep
from unittest.mock import Mock

from pycrunch.plugins.django_support.django_runner_engine import DjangoRunnerEngine


class MyFancyClass(object):

    def __init__(self, name):
        self.name = name

    def do_something(self):
        proc_name = multiprocessing.current_process().name
        pprint(len(list(sys.modules)))
        pprint('in sub^')

        print('Doing something fancy in %s for %s!' % (proc_name, self.name))


def run_in_separate_process(q, res):
    obj = q.get()
    obj.do_something()
    # sleep()
    from pycrunch import session
    ee = session.config.runtime_engine
    res.put(f'abc {len(list(sys.modules))}: engine: {ee}')
    res.put('bbb')


def run(file_task):
    from pycrunch.shared import TestMetadata

    from multiprocessing.connection import Client
    from pycrunch.runner.test_runner import TestRunner
    test_configuration = None
    tests_to_run = []
    if not file_task:
        address = ('localhost', 6001)
        conn = Client(address, authkey=b'secret password')
        tests_to_run = conn.recv()
    else:
        with open(file_task, 'r') as f:
            conn = Mock()
            task_def = f.read()
            test_configuration = task_def
            tests_to_run = json.loads(test_configuration)['tests']

    pprint(test_configuration)

    for t in tests_to_run:
        xxx = TestMetadata(**t)
        # conn.send('running ' + xxx.fqn)
    from pycrunch.plugins.pytest_support.pytest_runner_engine import PyTestRunnerEngine
    sys.path.insert(0, str(Path('.').absolute()))

    r = TestRunner(DjangoRunnerEngine())
    results = r.run(tests_to_run)
    conn.send(results)

    conn.send('close')
    # can also send arbitrary objects:
    # conn.send(['a', 2.5, None, int, sum])
    conn.close()

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='PyCrunch CLI')

    parser.add_argument('--file', help='The file instead of network socket')
    args = parser.parse_args()
    file_task = args.file

    with open('/Users/gleb/code/PyCrunch/child_process.log', 'a')  as file:
        file.writelines(['huita',''])
        file.write(os.linesep)

    print('zalupa')
    print(Path('.').absolute())
    run(file_task)