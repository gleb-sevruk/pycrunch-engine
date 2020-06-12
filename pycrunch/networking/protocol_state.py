import io
import pickle
import struct

class ProtocolState():
    def __init__(self, message_queue):
        self.message_queue = message_queue
        # what if header split?
        self.header_size = struct.calcsize("i")
        self.header_buffer = None
        self.in_header = False
        self.header_bytes_so_far = 0

        self.in_message = False
        self.message_bytes_so_far = 0
        self.message_bytes_total = 0
        self.buffer = None
        self.current_payload_size = 0
        self.current_payload_read_so_far = 0

    def feed(self, data):
        """
        This method is responsible for processing input datagrams
        Message may be splitted across multiple datagrams

        Here we read size of next packet from header with fixed byte-length
          and accumulating multiple packages until entire message is read

          also one datagram may contain multiple messages split by header
          so this function solves all of these scenarios
        """
        self.current_payload_size = len(data)
        # print(f'!!! GOT DATAGRAM, size: {self.current_payload_size}')

        self.current_payload_read_so_far = 0
        input_stream = io.BytesIO(data)
        while self.current_payload_read_so_far < self.current_payload_size:
            if not self.in_message:
                # print('reading header')
                if not self.header_buffer:
                    # print('creating new header buffer')
                    self.header_buffer = io.BytesIO()

                self.in_header = True
                # how much we can read?
                read_header_amount = self.header_size - self.header_bytes_so_far
                # print(f'read_header_amount {read_header_amount}')
                # print(f'header_bytes_so_far {self.header_bytes_so_far}')
                if self.current_payload_size - self.current_payload_read_so_far < read_header_amount:
                    read_header_amount = self.current_payload_size - self.current_payload_read_so_far

                message_header_bytes = input_stream.read(read_header_amount)
                self.header_buffer.write(message_header_bytes)
                self.header_bytes_so_far += read_header_amount
                self.current_payload_read_so_far += read_header_amount
                # print(f'current_payload_read_so_far {self.current_payload_read_so_far}')
                if self.header_bytes_so_far >= self.header_size:
                    getbuffer = self.header_buffer.getbuffer()
                    # print(f'self.header_buffer.len() {len(getbuffer)}')
                    self.message_bytes_total = struct.unpack('i', getbuffer.tobytes())[0]
                    # print(f'!!! Expecting message_bytes_total: {self.message_bytes_total}')
                    self.header_buffer = None
                    self.header_bytes_so_far = 0
                    self.in_header = False
                    self.in_message = True
                else:
                    # wait for other part of the header
                    break

            read_amount = self.message_bytes_total - self.message_bytes_so_far
            if self.message_bytes_total - self.message_bytes_so_far > self.current_payload_size - self.current_payload_read_so_far:
                read_amount = self.current_payload_size - self.current_payload_read_so_far

            if not self.buffer:
                # print('creating new buffer')
                self.buffer = io.BytesIO()

            self.buffer.write(input_stream.read(read_amount))
            self.current_payload_read_so_far += read_amount
            self.message_bytes_so_far += read_amount
            if self.message_bytes_so_far >= self.message_bytes_total:
                message = pickle.loads(self.buffer.getbuffer())
                # print(f'message read to the end - {message.kind}')

                self.buffer = None
                self.message_bytes_so_far = 0
                self.in_message = False

                self.message_queue.put_nowait(message)

            if self.current_payload_read_so_far >= self.current_payload_size:
                pass
        # print('read to the end')