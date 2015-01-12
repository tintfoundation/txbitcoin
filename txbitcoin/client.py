class BitcoinClient(BitcoinProtocol):
    def __init__(self):
        BitcoinProtocol.__init__(self)
        self.addObserver('version', self.handle_version)
        self.addObserver('ping', self.handle_ping)
        self.addObserver('inv', self.handle_inventory)

    def handle_inventory(self, message):
        print message

    def handle_version(self, message):
        print "Someone called version"
        self.send_message(VerAck())

    def handle_ping(self, message):
        print "someone called ping"
        pong = Pong()
        pong.nonce = message.nonce
        self.send_message(pong)
