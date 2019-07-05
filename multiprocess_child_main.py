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
from pycrunch.session import config


def run(file_task, engine_to_use):
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
    runner_engine = None
    # add root of django project
    sys.path.insert(0, str(Path('.').absolute()))

    from pycrunch.plugins.pytest_support.pytest_runner_engine import PyTestRunnerEngine
    if engine_to_use == 'pytest':
        runner_engine = PyTestRunnerEngine()
    elif engine_to_use == 'django':
        runner_engine = DjangoRunnerEngine()
    else:
        print('using default engine => pytest')
        runner_engine = PyTestRunnerEngine()



    r = TestRunner(runner_engine)
    results = r.run(tests_to_run)
    conn.send(results)

    conn.send('close')
    # can also send arbitrary objects:
    # conn.send(['a', 2.5, None, int, sum])
    conn.close()

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='PyCrunch CLI')

    parser.add_argument('--file', help='The file instead of network socket')
    parser.add_argument('--engine', help='Engine used, one of [pytest, django, simple]')
    args = parser.parse_args()
    file_task = args.file
    engine_to_use = args.engine
    if engine_to_use:
        config.runtime_engine_will_change(engine_to_use)
    with open(f'.{os.sep}child_process.log', 'a') as file:
        file.writelines(['huita',''])
        file.write(os.linesep)

    print('zalupa')
    print(Path('.').absolute())
    run(file_task=file_task, engine_to_use=engine_to_use)