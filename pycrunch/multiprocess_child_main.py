# Note to maintainers:
#   Important - no typying here to speed up process startup
#   If I add typing here or in any other file referenced by child process
#   it takes 0.36 additional seconds to start the process (on intel)

import asyncio
import sys

import nest_asyncio

nest_asyncio.apply()


async def run(engine_to_use, timeline, port, task_id):
    from pycrunch.child_runtime.client_protocol import EchoClientProtocol

    timeline.mark_event('Run: inside method, imports')
    import sys
    from pathlib import Path

    # from pprint import pprint
    # from multiprocessing.connection import Client
    # timeline.mark_event('Run: imported multiprocessing.connection')
    timeline.mark_event('Run: imported TestRunner')

    timeline.mark_event('Run: imports done')

    # test_configuration = None
    # tests_to_run = []
    # add root of django project
    sys.path.insert(0, str(Path('.').absolute()))
    # todo: make configurable instead
    # sys.path.insert(0, '/code')
    global loop

    on_con_lost = loop.create_future()
    timeline.mark_event('TCP: Opening connection')
    transport, protocol1 = await loop.create_connection(  # noqa F841
        lambda: EchoClientProtocol(on_con_lost, task_id, timeline, engine_to_use),
        '127.0.0.1',
        port,
    )
    await on_con_lost


async def main():
    # import pydevd_pycharm
    #
    # pydevd_pycharm.settrace('localhost', port=21345, stdoutToServer=True, stderrToServer=True)
    from pycrunch.introspection.timings import Timeline

    timeline = Timeline('multiprocess run engine')
    timeline.start()
    timeline.mark_event('__main__')

    timeline.mark_event('ArgumentParser: Init')
    import argparse

    parser = argparse.ArgumentParser(description='PyCrunch CLI')

    parser.add_argument('--engine', help='Engine used, one of [pytest, django, simple]')
    parser.add_argument('--port', help='PyCrunch-Engine server port to connect')
    parser.add_argument(
        '--task-id', help='Id of task when multiple test runners ran at same time'
    )
    parser.add_argument(
        '--load-pytest-plugins', help='If this is true, execution will be slower.'
    )
    parser.add_argument(
        '--enable-remote-debug',
        action='store_true',
        help='If this is true, remote debug will be enabled on a --remote-debugger-port',
    )
    parser.add_argument(
        '--remote-debugger-port',
        help='If remote debug is enabled, this will specify a port used to connect to PyCharm pudb',
    )
    parser.add_argument(
        '--collect-perf',
        action='store_true',
        help='If this is enabled, timings/timelines will be collected and sent to web_ui for further look',
    )
    args = parser.parse_args()
    timeline.mark_event('ArgumentParser: parse_args completed')
    from pycrunch.child_runtime.child_config import child_config

    engine_to_use = args.engine
    if args.engine:
        child_config.use_engine(engine_to_use)
    if args.load_pytest_plugins.lower() == 'true':
        child_config.load_pytest_plugins = True
    if args.enable_remote_debug:
        child_config.enable_remote_debugging(args.remote_debugger_port)
    if args.collect_perf:
        child_config.enable_timing_collection()

    timeline.mark_event('Before run')

    await run(
        engine_to_use=engine_to_use,
        timeline=timeline,
        port=args.port,
        task_id=args.task_id,
    )


if sys.version_info >= (3, 10):
    # Python 3.10 or newer
    loop = asyncio.new_event_loop()

    try:
        asyncio.set_event_loop(loop)
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print('graceful quit!')
        pass
    finally:
        loop.close()
else:
    # Python 3.9 or older
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print('graceful quit!')
        pass
    finally:
        loop.close()
