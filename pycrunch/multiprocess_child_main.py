import asyncio
from os import environ

from pycrunch.introspection.timings import Timeline
import argparse

from pycrunch.scheduling.client_protocol import EchoClientProtocol


async def run(engine_to_use, timeline, port, task_id):
    timeline.mark_event('Run: inside method, imports')
    import json
    import sys
    from pathlib import Path
    # from pprint import pprint
    # from multiprocessing.connection import Client
    # timeline.mark_event('Run: imported multiprocessing.connection')
    from pycrunch.runner.test_runner import TestRunner
    timeline.mark_event('Run: imported TestRunner')

    timeline.mark_event('Run: imports done')

    test_configuration = None
    tests_to_run = []
    # add root of django project
    sys.path.insert(0, str(Path('.').absolute()))
    # todo ???
    sys.path.insert(0, '/code')

    loop = asyncio.get_event_loop()

    # todo : should be dynamic
    on_con_lost = loop.create_future()
    timeline.mark_event('TCP: Opening connection')
    transport, protocol1 = await loop.create_connection(
        lambda: EchoClientProtocol(on_con_lost, task_id, timeline, engine_to_use),
        '127.0.0.1', port)
    # tests_to_run = conn.recv()
    await on_con_lost


async def main():
    # import pydevd_pycharm
    #
    # pydevd_pycharm.settrace('localhost', port=21345, stdoutToServer=True, stderrToServer=True)

    timeline = Timeline('multiprocess run engine')
    timeline.start()
    timeline.mark_event('__main__')

    timeline.mark_event('ArgumentParser: Init')

    parser = argparse.ArgumentParser(description='PyCrunch CLI')

    parser.add_argument('--engine', help='Engine used, one of [pytest, django, simple]')
    parser.add_argument('--port', help='PyCrunch-Engine server port to connect')
    parser.add_argument('--task-id', help='Id of task when multiple test runners ran at same time')

    args = parser.parse_args()
    timeline.mark_event('ArgumentParser: parse_args completed')
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

    await run(engine_to_use=engine_to_use, timeline=timeline, port=args.port, task_id=args.task_id)


loop = asyncio.get_event_loop()

try:
    loop.run_until_complete(main())
    # loop.run_forever()
except KeyboardInterrupt:
    print('graceful quit!')
    pass