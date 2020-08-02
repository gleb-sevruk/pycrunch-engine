
import asyncio
import io
import pickle
import struct
from queue import Queue, Empty

from pycrunch.introspection.history import execution_history
from pycrunch.networking.protocol_state import ProtocolState
from pycrunch.scheduling.messages import ScheduledTaskDefinitionMessage

import logging

logger = logging.getLogger(__name__)


class TestRunnerServerProtocol(asyncio.Protocol):
    # 1 object - 1 connection
    def __init__(self, tasks, completion_future, timeline):
        self.timeline = timeline
        self.completion_future = completion_future
        self.tasks = tasks
        self.transport = None
        # Will be determined after handshake
        self.task_id = None
        self.message_queue = Queue()
        self.results = []
        self.need_more_data = False
        self.message_length = 0
        self.read_so_far = 0
        self.message_buffer = None
        self.state_machine = ProtocolState(self.message_queue)

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        logger.debug(f'Connection from {peername}')
        self.transport = transport

    def feed_datagram(self, data):
        self.state_machine.feed(data)

    def data_received(self, data):
        self.feed_datagram(data)
        self.process_messages()

    def process_messages(self):
        while True:
            msg = self.try_get_next_message()
            if not msg:
                break

            self.process_single_message(msg)


    def process_single_message(self, msg):
        logger.info(f'process_single_message - {msg.kind}')
        if msg.kind == 'handshake':
            found_task = self.find_task_with_id(msg)
            if found_task is None:
                raise Exception('no task found for subprocess. ')

            logger.debug(f'sending task definition, {found_task.id}')
            msg_to_reply = ScheduledTaskDefinitionMessage(task=found_task)
            bytes_msg = pickle.dumps(msg_to_reply)
            self.transport.write(bytes_msg)
        if msg.kind == 'test_run_results':
            results = msg.results
            self.timeline.mark_event('TCP: Got test run results from subprocess')
            self.results_did_become_available(results)
        if msg.kind == 'timings':
            self.timeline.mark_event('TCP: Got timings from subprocess')
            execution_history.save(msg.timeline)
        if msg.kind == 'close':
            self.timeline.mark_event('TCP: Received close message')
            logger.debug('Close the client socket')
            self.transport.close()
            self.completion_future.set_result(self.results)

    def try_get_next_message(self):
        msg = None
        try:
            msg = self.message_queue.get_nowait()
        except Empty as e:
            pass
            # print('process_messages: nothing to process')
        return msg

    def connection_lost(self, ex = None):
        if not self.completion_future.done():
            self.completion_future.set_result(self.results)

    def find_task_with_id(self, msg):
        found_task = None
        for x in self.tasks:
            if x.id == msg.task_id:
                found_task = x
                break
        return found_task

    def results_did_become_available(self, results):
        self.results = results

    def force_close(self):
        self.transport.close()
        self.completion_future.cancel()

