import asyncio
import pickle

import pytest

from pycrunch.scheduling.concurrent_multiprocess_run import ConcurrentMultiprocessTestRunner, HandshakeMessage, CloseConnectionMessage
from pycrunch.scheduling.sheduled_task import TestRunPlan
from pycrunch.tests.test_scheduling import generate_tests

# async def tcp_echo_client(message):
#     reader, writer = await asyncio.open_connection('127.0.0.1', 8888)
#
#     print('Send: %r' % message)
#     writer.write(message.encode())
#
#     data = await reader.read(100)
#     print('Received: %r' % data.decode())
#
#     print('Close the socket')
#     writer.close()

class EchoClientProtocol(asyncio.Protocol):
    def __init__(self, on_connection_lost, task_id):
        self.task_id = task_id
        self.on_con_lost = on_connection_lost
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport
        msg = HandshakeMessage(self.task_id)
        msg_bites = pickle.dumps(msg)
        print(f'Data sent: {msg.task_id}')
        # transport.write(b'x')
        transport.write(msg_bites)


    def data_received(self, data):
        msg = pickle.loads(data)
        if msg.kind == 'test-run-task':
            print(f'Data received: test-run-task')
            print(f'task_id: {msg.task.id}')
            send_this = CloseConnectionMessage(self.task_id)
            bytes_to_send = pickle.dumps(send_this)
            self.transport.write(bytes_to_send)

    def connection_lost(self, exc):
        print('The server closed the connection')
        self.on_con_lost.set_result(True)

    def error_received(self, exc):
        print('Error received:', exc)


@pytest.mark.asyncio
async def test_connection_is_made():
    tests = generate_tests(1)
    plan = []
    plan.append(TestRunPlan(tests))

    sut = ConcurrentMultiprocessTestRunner()
    loop = asyncio.get_event_loop()

    on_con_lost = loop.create_future()
    message = 'Hello World!'
    for x in range(10):
        message += str(x)
    # await future_x
    server_task = loop.create_task(sut.run(plan))
    await asyncio.sleep(1)
    transport, protocol = await loop.create_connection(
        lambda: EchoClientProtocol(on_con_lost, plan[0].id),
        '127.0.0.1', 8888)

    # Wait until the protocol signals that the connection
    # is lost and close the transport.
    try:
        await server_task
        await on_con_lost
    finally:
        transport.close()