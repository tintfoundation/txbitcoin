import os

from twisted.internet.protocol import Protocol
from twisted.python import log

from protocoin.serializers import *


class BitcoinProtocol(Protocol):
    coin = "bitcoin"

    def __init__(self):
        self.buffer = StringIO()
        self.observers = {}
        self.addObserver('version', self.handle_version)
        self.addObserver('verack', self.handle_verack)
        self.addObserver('ping', self.handle_ping)
        self.addObserver('inv', self.handle_inventory)

    def handle_verack(self, message):
        self.factory.connectionMade()

    def handle_version(self, message):
        log.msg("Got version %s" % str(message.user_agent))
        self.send_message(VerAck())

    def handle_ping(self, message):
        pong = Pong()
        pong.nonce = message.nonce
        self.send_message(pong)

    def handle_inventory(self, message):
        log.msg("Got some inventory: ")
        log.msg(message)

    def get_blocks(self, blocks):
        # convert hashes to ints
        blocks = map(lambda h: int(h, 16), blocks)
        gb = GetBlocks(blocks)
        self.send_message(gb)

    def addObserver(self, command, func):
        if command not in self.observers:
            self.observers[command] = []
        self.observers[command].append(func)

    def emit(self, command, message):
        if command not in self.observers:
            log.msg("No handlers for command %s" % command)
            return
        for func in self.observers[command]:
            func(message)

    def send_message(self, message):
        log.msg("Sending message %s" % message.command)
        message_header = MessageHeader(self.coin)
        message_header_serial = MessageHeaderSerializer()
        serializer = MESSAGE_MAPPING[message.command]()
        bin_message = serializer.serialize(message)
        payload_checksum = MessageHeaderSerializer.calc_checksum(bin_message)
        message_header.checksum = payload_checksum
        message_header.length = len(bin_message)
        message_header.command = message.command
        self.transport.write(message_header_serial.serialize(message_header))
        self.transport.write(bin_message)
        
    def dataReceived(self, data):
        self.buffer.write(data)

        # Calculate the size of the buffer
        self.buffer.seek(0, os.SEEK_END)
        buffer_size = self.buffer.tell()

        # Check if a complete header is present
        if buffer_size < MessageHeaderSerializer.calcsize():
            return

        # Go to the beginning of the buffer
        self.buffer.reset()

        message_model = None
        message_header_serial = MessageHeaderSerializer()
        message_header = message_header_serial.deserialize(self.buffer)
        total_length = MessageHeaderSerializer.calcsize() + message_header.length

        # Incomplete message
        if buffer_size < total_length:
            self.buffer.seek(0, os.SEEK_END)
            return

        payload = self.buffer.read(message_header.length)
        remaining = self.buffer.read()
        self.buffer = StringIO()
        self.buffer.write(remaining)
        payload_checksum = MessageHeaderSerializer.calc_checksum(payload)

        # Check if the checksum is valid
        if payload_checksum != message_header.checksum:
            raise RuntimeError("Bad Checksum!")

        if message_header.command in MESSAGE_MAPPING:
            deserializer = MESSAGE_MAPPING[message_header.command]()
            message_model = deserializer.deserialize(StringIO(payload))

        log.msg("Got message: %s" % message_header.command)
        self.emit(message_header.command, message_model)

    def connectionMade(self):
        v = Version()
        v.user_agent = "/txbitcoin:0.0.1/"
        self.send_message(v)
