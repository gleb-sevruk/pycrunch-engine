import asyncio
import pickle


class AbstractMessage():
    kind = 'abstract'


class HandshakeMessage(AbstractMessage):
    def __init__(self, task_id):
        self.task_id = task_id
        self.kind = 'handshake'

class ScheduledTaskDefinitionMessage(AbstractMessage):
    def __init__(self, task):
        self.task = task
        self.kind = 'test-run-task'

class CloseConnectionMessage(AbstractMessage):
    def __init__(self, task_id):
        self.task_id = task_id
        self.kind = 'close'

class EchoServerProtocol(asyncio.Protocol):
    def __init__(self, tasks):
        self.tasks = tasks

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        print('Connection from {}'.format(peername))
        self.transport = transport
        # transport.write(b'x')

    def data_received(self, data):
        msg = pickle.loads(data) # type AbstractMessage
        print('Data received: ' + format(msg.kind))
        if msg.kind == 'handshake':
            found_task = self.find_task_with_id(msg)
            if found_task is None:
                raise Exception('chto vi ludi delaete?')

            print('sending task definition, ' + found_task.id)
            msg_to_reply = ScheduledTaskDefinitionMessage(task=found_task)
            bytes_msg = pickle.dumps(msg_to_reply)
            self.transport.write(bytes_msg)
        if msg.kind == 'close':
            print('Close the client socket')
            self.transport.close()

    def find_task_with_id(self, msg):
        found_task = None
        for x in self.tasks:
            if x.id == msg.task_id:
                print("i found it!, " + x.id)
                found_task = x
                break
        return found_task


class ConcurrentMultiprocessTestRunner():
    def __init__(self):
        pass

    async def run(self, tasks):
        loop = asyncio.get_event_loop()
        # todo - create future and pass it to server.
        # when all clients are done - complete this future
        # on cancellation request future will be completed also, killing all subprocesses
        # combine results from all processes into single array and send combined coverage
        server = await loop.create_server(
            lambda: EchoServerProtocol(tasks),
            '127.0.0.1', 8888)
        await asyncio.sleep(0.1)
        print('before await')
        await asyncio.sleep(3.1)
        server.close()
        print('after await')
