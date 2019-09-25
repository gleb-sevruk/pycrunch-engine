import asyncio

from pycrunch.scheduling.concurrent_multiprocess_run import EchoServerProtocol
from pycrunch.scheduling.sheduled_task import TestRunPlan
from pycrunch.tests.test_scheduling import generate_tests

tests = generate_tests(3)
plan = []
plan.append(TestRunPlan(tests, id='1'))
plan.append(TestRunPlan(tests, id='2'))
plan.append(TestRunPlan(tests, id='3'))

loop = asyncio.get_event_loop()

coro = loop.create_server(
    lambda: EchoServerProtocol(plan),
    '127.0.0.1', 8888)

server = loop.run_until_complete(coro)

print(server)
print('Serving on 8888')
print('Ctrl+C to gracefully quit')

try:
    loop.run_forever()
except KeyboardInterrupt:
    print('graceful quit!')
    pass

server.close()
loop.run_until_complete(server.wait_closed())
loop.close()
