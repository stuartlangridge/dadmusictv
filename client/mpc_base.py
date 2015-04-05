class MPCClient(object):
    def __init__(self, host, port, outq):
        self.host = host
        self.port = int(port)
        self.outq = outq
        self.connect()

    def connect(self):
        raise NotImplemented
