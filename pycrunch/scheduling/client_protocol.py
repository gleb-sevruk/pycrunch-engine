import asyncio
import pickle
import struct
import time

from pycrunch.runner.test_runner import TestRunner
from pycrunch.scheduling.messages import CloseConnectionMessage, HandshakeMessage, TestResultsAvailableMessage, TestRunTimingsMessage

counter = 0


class EchoClientProtocol(asyncio.Protocol):

    def __init__(self, on_connection_lost, task_id, timeline, engine_to_use):
        self.engine_to_use = engine_to_use
        self.timeline = timeline
        self.task_id = task_id
        self.on_con_lost = on_connection_lost
        self.transport = None
        global counter
        self.connection_counter = counter+1
        counter += 1

    def connection_made(self, transport):
        self.transport = transport
        msg = HandshakeMessage(self.task_id)
        msg_bites = pickle.dumps(msg)
        # print(f'[{self.connection_counter}]Handshake sent: {msg.task_id}')
        self.send_with_header(msg_bites)



    def data_received(self, data):
        # asyncio.sleep(2)
        msg = pickle.loads(data)
        if msg.kind == 'test-run-task':
            # import pydevd_pycharm
            # pydevd_pycharm.settrace('localhost', port=21345, stdoutToServer=True, stderrToServer=True)
            print(f'[{msg.task.id}]Data received: test-run-task;')
            timeline = self.timeline
            timeline.mark_event(f'TCP: Received tests to run; id: {msg.task.id}')

            runner_engine = None
            # add root of django project

            timeline.mark_event('Deciding on runner engine...')

            from pycrunch.plugins.pytest_support.pytest_runner_engine import PyTestRunnerEngine
            if self.engine_to_use == 'pytest':
                runner_engine = PyTestRunnerEngine()
            elif self.engine_to_use == 'django':
                from pycrunch.plugins.django_support.django_runner_engine import DjangoRunnerEngine
                runner_engine = DjangoRunnerEngine()
            else:
                print('using default engine => pytest')
                runner_engine = PyTestRunnerEngine()

            # should have env from pycrunch config
            # print(environ)

            r = TestRunner(runner_engine, timeline)
            timeline.mark_event(f'Run: about to run tests')
            try:
                timeline.mark_event(f'Run: total tests planned: {len(msg.task.tests)}')
                results = r.run(msg.task.tests)
                timeline.mark_event('Run: Completed, sending results')

                # import pydevd_pycharm
                # pydevd_pycharm.settrace('localhost', port=21345, stdoutToServer=True, stderrToServer=True)
                msg = TestResultsAvailableMessage(results)
                bytes_to_send = pickle.dumps(msg)
                self.send_with_header(bytes_to_send)
                timeline.mark_event('TCP: results sent')
                # conn.send(TcpMessage(kind='test_run_results', data_to_send=results))
            except Exception as e:
                timeline.mark_event('Run: exception during execution')

            timeline.stop()
            # timeline.to_console()
            # time.sleep(0.01)
            msg = TestRunTimingsMessage(timeline)
            bytes_to_send1 = pickle.dumps(msg)
            # xxx = bytearray(12345678)
            self.send_with_header(bytes_to_send1)

            # time.sleep(0.01)
            msg = CloseConnectionMessage(self.task_id)
            bytes_to_send2 = pickle.dumps(msg)
            self.send_with_header(bytes_to_send2)

    def send_with_header(self, bytes_to_send):
        # we use format: {length}{payload} to deal with TCP coalescing
        length_of_message = len(bytes_to_send)
        header_bytes = struct.pack("i", length_of_message)
        self.transport.write(header_bytes + bytes_to_send)

    def mark_all_done(self):
        # print(f'[{self.connection_counter}] mark_all_done')

        send_this = CloseConnectionMessage(self.task_id)
        bytes_to_send = pickle.dumps(send_this)
        self.send_with_header(bytes_to_send)

    def connection_lost(self, exc):
        print(f'[{self.task_id}]The connection to server closed')
        self.on_con_lost.set_result(True)

    def error_received(self, exc):
        print('Error received:', exc)

