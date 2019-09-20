from os import environ

from pycrunch.introspection.timings import Timeline
import argparse


def run(file_task, engine_to_use, timeline):
    timeline.mark_event('Run: inside method, imports')
    import json
    import sys
    from pathlib import Path
    # from pprint import pprint
    from unittest.mock import Mock

    from pycrunch.crossprocess.tcp_message import TcpMessage

    from multiprocessing.connection import Client
    timeline.mark_event('Run: imported multiprocessing.connection')
    from pycrunch.runner.test_runner import TestRunner
    timeline.mark_event('Run: imported TestRunner')

    timeline.mark_event('Run: imports done')

    test_configuration = None
    tests_to_run = []
    if not file_task:
        timeline.mark_event('TCP: Opening connection')
        # todo : should be dynamic
        address = ('localhost', 6001)
        conn = Client(address, authkey=b'secret password')
        tests_to_run = conn.recv()
        timeline.mark_event('TCP: Received tests to run')

    else:
        with open(file_task, 'r') as f:
            conn = Mock()
            task_def = f.read()
            test_configuration = task_def
            tests_to_run = json.loads(test_configuration)['tests']

    # pprint(test_configuration)

    runner_engine = None
    # add root of django project
    sys.path.insert(0, str(Path('.').absolute()))
    # todo ???
    sys.path.insert(0, '/code')

    timeline.mark_event('Deciding on runner engine...')

    from pycrunch.plugins.pytest_support.pytest_runner_engine import PyTestRunnerEngine
    if engine_to_use == 'pytest':
        runner_engine = PyTestRunnerEngine()
    elif engine_to_use == 'django':
        from pycrunch.plugins.django_support.django_runner_engine import DjangoRunnerEngine
        runner_engine = DjangoRunnerEngine()
    else:
        print('using default engine => pytest')
        runner_engine = PyTestRunnerEngine()

    # should have env from pycrunch config
    # print(environ)

    r = TestRunner(runner_engine, timeline)
    timeline.mark_event('Run: about to run tests')
    try:
        results = r.run(tests_to_run)
        timeline.mark_event('Run: Completed, sending results')

        # import pydevd_pycharm
        # pydevd_pycharm.settrace('localhost', port=21345, stdoutToServer=True, stderrToServer=True)
        conn.send(TcpMessage(kind='test_run_results', data_to_send=results))
        timeline.mark_event('TCP: send complete')
    except Exception as e:
        timeline.mark_event('Run: exception during execution')

    timeline.stop()
    # timeline.to_console()
    conn.send(TcpMessage(kind='timings', data_to_send=timeline))

    conn.send('close')

    # can also send arbitrary objects:
    # conn.send(['a', 2.5, None, int, sum])

    conn.close()


if __name__ == '__main__':
    # import pydevd_pycharm
    #
    # pydevd_pycharm.settrace('localhost', port=21345, stdoutToServer=True, stderrToServer=True)

    timeline = Timeline('multiprocess run engine')
    timeline.start()
    timeline.mark_event('__main__')

    timeline.mark_event('ArgumentParser: Init')

    parser = argparse.ArgumentParser(description='PyCrunch CLI')

    parser.add_argument('--file', help='The file instead of network socket')
    parser.add_argument('--engine', help='Engine used, one of [pytest, django, simple]')

    args = parser.parse_args()
    timeline.mark_event('ArgumentParser: parse_args completed')
    file_task = args.file
    engine_to_use = args.engine
    if engine_to_use:
        from pycrunch.session import config

        config.runtime_engine_will_change(engine_to_use)
    # with open(f'.{os.sep}child_process.log', 'a') as file:
    #     file.writelines(['huita',''])
    #     file.write(os.linesep)
    #
    # print(Path('.').absolute())
    timeline.mark_event('Before run')

    run(file_task=file_task, engine_to_use=engine_to_use, timeline=timeline)