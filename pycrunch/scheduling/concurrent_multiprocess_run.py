import asyncio
import pickle

from pycrunch.scheduling.server_protocol import EchoServerProtocol



class ConcurrentMultiprocessTestRunner():
    def __init__(self, tasks):
        self.tasks = tasks
        self.client_futures = []

    async def run(self):
        loop = asyncio.get_event_loop()
        # todo - create future and pass it to server.
        # when all clients are done - complete this future
        # on cancellation request future will be completed also, killing all subprocesses
        # combine results from all processes into single array and send combined coverage
        server = await loop.create_server(
            lambda: self.create_server_protocol(),
            '127.0.0.1', 8888)
        await asyncio.sleep(0.1)
        print('before await')
        await asyncio.sleep(2.1)
        await asyncio.wait(self.client_futures)
        server.close()
        print('after await')

    def create_server_protocol(self):
        loop = asyncio.get_event_loop()
        completion_future = loop.create_future()
        self.client_futures.append(completion_future)
        return EchoServerProtocol(self.tasks, completion_future, Timeline())
