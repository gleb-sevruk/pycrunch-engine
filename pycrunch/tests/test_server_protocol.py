import io
import pickle
import struct
from unittest import TestCase
from unittest.mock import Mock

from pycrunch.scheduling.messages import HandshakeMessage
from pycrunch.networking.server_protocol import TestRunnerServerProtocol
from pycrunch.scheduling.sheduled_task import TestRunPlan
from pycrunch.tests.test_scheduling import generate_tests


class ServerProtocolTests(TestCase):
    def setUp(self) -> None:
        tests = generate_tests(3)
        self.plan = []
        self.plan.append(TestRunPlan(tests, id='1'))
        self.plan.append(TestRunPlan(tests, id='2'))
        self.plan.append(TestRunPlan(tests, id='3'))

    def test_single_message(self):
        sut = self.create_sut()
        transport = Mock()
        sut.connection_made(transport)

        print(struct.calcsize("i"))
        handshake = HandshakeMessage('42')
        msg = pickle.dumps(handshake)
        header_bytes = struct.pack("i", len(msg))
        sut.feed_datagram(header_bytes + msg)
        msg = list(sut.message_queue.queue)
        assert msg[0].kind == 'handshake'
        assert msg[0].task_id == '42'

    def test_multiple_messages_in_one_payload(self):
        sut = self.create_sut()
        transport = Mock()
        sut.connection_made(transport)

        handshake = HandshakeMessage('43')
        msg = pickle.dumps(handshake)
        header_bytes = struct.pack("i", len(msg))

        handshake = HandshakeMessage('44')
        msg2 = pickle.dumps(handshake)
        header_bytes2 = struct.pack("i", len(msg))

        sut.feed_datagram(header_bytes + msg + header_bytes2 + msg2)
        message_queue = list(sut.message_queue.queue)
        assert len(message_queue) == 2
        assert message_queue[0].task_id == '43'
        assert message_queue[1].task_id == '44'

    def test_message_split_into_two_packets(self):
        sut = self.create_sut()
        transport = Mock()
        sut.connection_made(transport)

        handshake = HandshakeMessage('43')
        msg = pickle.dumps(handshake)
        length_of_message = len(msg)
        header_bytes = struct.pack("i", length_of_message)
        half = round(length_of_message / 2)
        print(length_of_message)
        msg_1 = msg[:half]
        msg_2 = msg[half:]

        print(msg_1)
        print(msg_2)

        recovered_bytes = msg_1 + msg_2
        msg_recovered = pickle.loads(recovered_bytes)
        print(msg_recovered)
        print(msg_recovered.task_id)
        sut.feed_datagram(header_bytes + msg_1)
        sut.feed_datagram(msg_2)
        message_queue = list(sut.message_queue.queue)
        assert len(message_queue) == 1

        pass

    def test_message_split_into_three_packets_with_overrun_message(self):
        sut = self.create_sut()
        transport = Mock()
        sut.connection_made(transport)

        handshake = HandshakeMessage('43')
        msg = pickle.dumps(handshake)
        length_of_message = len(msg)
        header_bytes = struct.pack("i", length_of_message)
        half = round(length_of_message / 2)
        print(length_of_message)
        msg_1 = msg[:half]
        msg_2 = msg[half:]

        print(msg_1)
        print(msg_2)

        handshake2 = HandshakeMessage('44')
        msg4_bytes = pickle.dumps(handshake2)
        length_of_message2 = len(msg4_bytes)
        header_bytes2 = struct.pack("i", length_of_message2)
        half2 = round(length_of_message2 / 2)
        msg_3 = msg4_bytes[:half]
        msg_4 = msg4_bytes[half:]

        recovered_bytes = msg_1 + msg_2
        msg_recovered = pickle.loads(recovered_bytes)
        print(msg_recovered)
        print(msg_recovered.task_id)
        sut.feed_datagram(header_bytes + msg_1)
        sut.feed_datagram(msg_2 + header_bytes2)
        sut.feed_datagram(msg_3)
        sut.feed_datagram(msg_4)
        message_queue = list(sut.message_queue.queue)
        assert len(message_queue) == 2
        assert message_queue[0].task_id == '43'
        assert message_queue[1].task_id == '44'

        pass

    def test_message_header_split_into_packets(self):
        # -> {length}{buffer}{length}{buffer}
        # <- {length}{buffer}{len
        # <-  gth}{buffer}
        sut = self.create_sut()
        transport = Mock()
        sut.connection_made(transport)

        handshake = HandshakeMessage('43')
        msg = pickle.dumps(handshake)
        length_of_message = len(msg)
        header_bytes = struct.pack("i", length_of_message)
        half = round(length_of_message / 2)
        print(length_of_message)
        msg_1 = msg[:half]
        msg_2 = msg[half:]

        print(msg_1)
        print(msg_2)

        handshake2 = HandshakeMessage('44')
        msg4_bytes = pickle.dumps(handshake2)
        length_of_message2 = len(msg4_bytes)
        header_bytes2 = struct.pack("i", length_of_message2)
        half2 = round(length_of_message2 / 2)
        msg_3 = msg4_bytes[:half]
        msg_4 = msg4_bytes[half:]

        recovered_bytes = msg_1 + msg_2
        msg_recovered = pickle.loads(recovered_bytes)
        print(msg_recovered)
        print(msg_recovered.task_id)
        sut.feed_datagram(header_bytes + msg_1)
        sut.feed_datagram(msg_2 + header_bytes2[:2])
        sut.feed_datagram(header_bytes2[2:] + msg_3)
        sut.feed_datagram(msg_4)
        message_queue = list(sut.message_queue.queue)
        assert len(message_queue) == 2
        assert message_queue[0].task_id == '43'
        assert message_queue[1].task_id == '44'

        pass

    def create_sut(self):
        sut = TestRunnerServerProtocol(self.plan, Mock(), Mock())
        sut.process_messages = Mock()
        return sut

    def test_random_bytes(self):
        # -> {length}{buffer}{length}{buffer}
        # <- {length}{buffer}{len
        # <-  gth}{buffer}
        sut = self.create_sut()
        transport = Mock()
        sut.connection_made(transport)
        stream = io.BytesIO()

        stream.write(self.transport_message_bytes(HandshakeMessage('43')))
        stream.write(self.transport_message_bytes(HandshakeMessage('44')))
        stream.write(self.transport_message_bytes(HandshakeMessage('45')))
        stream.write(self.transport_message_bytes(HandshakeMessage('45')))
        stream.write(self.transport_message_bytes(HandshakeMessage('45')))
        stream.write(self.transport_message_bytes(HandshakeMessage('49')))
        buf = stream.getbuffer()
        print(f'lll {len(buf)}')
        read_stream = io.BytesIO(buf.tobytes())

        while True:
            current_byte = read_stream.read(3)
            if len(current_byte) == 0:
                break

            sut.feed_datagram(current_byte)

        # sut.feed_datagram(msg_2 + header_bytes2[:2])
        # sut.feed_datagram(header_bytes2[2:] + msg_3)
        # sut.feed_datagram(msg_4)
        message_queue = list(sut.message_queue.queue)
        assert len(message_queue) == 6
        assert message_queue[0].task_id == '43'
        assert message_queue[1].task_id == '44'
        assert message_queue[5].task_id == '49'

        pass

    def transport_message_bytes(self, msg):
        msg_bytes= pickle.dumps(msg)
        length_of_message = len(msg_bytes)
        header_bytes2 = struct.pack("i", length_of_message)
        return header_bytes2+msg_bytes