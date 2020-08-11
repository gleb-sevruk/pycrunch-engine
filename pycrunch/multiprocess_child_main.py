import asyncio

from pycrunch.introspection.timings import Timeline
import argparse

from pycrunch.child_runtime.client_protocol import EchoClientProtocol


async def run(engine_to_use, timeline, port, task_id):
    timeline.mark_event('Run: inside method, imports')
    import sys
    from pathlib import Path
    # from pprint import pprint
    # from multiprocessing.connection import Client
    # timeline.mark_event('Run: imported multiprocessing.connection')
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
    parser.add_argument('--load-pytest-plugins', help='If this is true, execution will be slower.')
    parser.add_argument('--enable-remote-debug', action='store_true', help='If this is true, remote debug will be enabled on a --remote-debugger-port')
    parser.add_argument('--remote-debugger-port', help='If remote debug is enabled, this will specify a port used to connect to PyCharm pudb')
    args = parser.parse_args()
    timeline.mark_event('ArgumentParser: parse_args completed')
    engine_to_use = args.engine
    if engine_to_use:
        from pycrunch.child_runtime.child_config import child_config
        child_config.use_engine(engine_to_use)
        if args.load_pytest_plugins.lower() == 'true':
            child_config.load_pytest_plugins = True
        if args.enable_remote_debug:
            child_config.enable_remote_debugging(args.remote_debugger_port)

    timeline.mark_event('Before run')

    await run(engine_to_use=engine_to_use, timeline=timeline, port=args.port, task_id=args.task_id)


loop = asyncio.get_event_loop()

try:
    loop.run_until_complete(main())
    # loop.run_forever()
except KeyboardInterrupt:
    print('graceful quit!')
    pass