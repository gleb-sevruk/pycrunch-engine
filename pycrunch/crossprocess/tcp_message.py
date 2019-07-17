class TcpMessage:
    def __init__(self, kind, data_to_send):
        self.data_to_send = data_to_send
        self.kind = kind
        
