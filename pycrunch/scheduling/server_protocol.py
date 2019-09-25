
import asyncio
import pickle

from pycrunch.introspection.history import execution_history
from pycrunch.scheduling.messages import ScheduledTaskDefinitionMessage


class EchoServerProtocol(asyncio.Protocol):
    # 1 object - 1 connection
    def __init__(self, tasks, completion_future, timeline):
        self.timeline = timeline
        self.completion_future = completion_future
        self.tasks = tasks
        self.transport = None
        # Will be determined after handshake
        self.task_id = None

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        print(f'Connection from {peername}')
        print(transport)
        self.transport = transport

    def data_received(self, data):
        msg = pickle.loads(data) # type AbstractMessage
        print('Data received: ' + format(msg.kind))
        if msg.kind == 'handshake':
            found_task = self.find_task_with_id(msg)
            if found_task is None:
                raise Exception('no task found for subprocess. ')

            print('sending task definition, ' + found_task.id)
            msg_to_reply = ScheduledTaskDefinitionMessage(task=found_task)
            bytes_msg = pickle.dumps(msg_to_reply)
            self.transport.write(bytes_msg)
        if msg.kind == 'test_run_results':
            results = msg.results
            self.timeline.mark_event('TCP: Got test run results from subprocess')
            self.results_did_become_available(results)
            self.completion_future.set_result(results)
        if msg.kind == 'timings':
            self.timeline.mark_event('TCP: Got timings from subprocess')
            execution_history.save(msg.timeline)
        if msg.kind == 'close':
            print('Close the client socket')
            self.transport.close()
            # self.completion_future.set_result(True)

    def find_task_with_id(self, msg):
        found_task = None
        for x in self.tasks:
            if x.id == msg.task_id:
                found_task = x
                break
        return found_task

    def results_did_become_available(self, results):
        self.results = results

