# import asyncio
# import pickle
# import time
#
# import pytest
#
# from pycrunch.introspection.timings import Timeline
# from pycrunch.scheduling.client_protocol import EchoClientProtocol
# from pycrunch.scheduling.sheduled_task import TestRunPlan
# from pycrunch.tests.test_scheduling import generate_tests
#
# # async def tcp_echo_client(message):
# #     reader, writer = await asyncio.open_connection('127.0.0.1', 8888)
# #
# #     print('Send: %r' % message)
# #     writer.write(message.encode())
# #
# #     data = await reader.read(100)
# #     print('Received: %r' % data.decode())
# #
# #     print('Close the socket')
# #     writer.close()
#
# @pytest.mark.asyncio
# async def test_connection_is_made():
#     tests = generate_tests(3)
#     plan = []
#     plan.append(TestRunPlan(tests, id='1'))
#     plan.append(TestRunPlan(tests, id='2'))
#     plan.append(TestRunPlan(tests, id='3'))
#
#     sut = ConcurrentMultiprocessTestRunner(plan)
#     loop = asyncio.get_event_loop()
#
#     on_con_lost = loop.create_future()
#     on_con_lost2 = loop.create_future()
#     on_con_lost3 = loop.create_future()
#     message = 'Hello World!'
#     for x in range(10):
#         message += str(x)
#     # await future_x
#     # server_task = loop.create_task(sut.run(plan))
#     # await asyncio.sleep(0.1)
#     t = Timeline('test run fake')
#     t.start()
#     transport, protocol1 = await loop.create_connection(
#         lambda: EchoClientProtocol(on_con_lost, plan[0].id, t),
#         '127.0.0.1', 8888)
#
#     transport2, protocol2 = await loop.create_connection(
#         lambda: EchoClientProtocol(on_con_lost2, plan[1].id, t),
#         '127.0.0.1', 8888)
#
#     transport3, protocol3 = await loop.create_connection(
#         lambda: EchoClientProtocol(on_con_lost3, plan[2].id, t),
#         '127.0.0.1', 8888)
#     # Wait until the protocol signals that the connection
#     # is lost and close the transport.
#     await asyncio.sleep(3)
#     protocol1.mark_all_done()
#     protocol2.mark_all_done()
#     protocol3.mark_all_done()
#     try:
#         await on_con_lost
#         await on_con_lost2
#         await on_con_lost3
#     finally:
#         transport.close()
#         transport2.close()
#         transport3.close()