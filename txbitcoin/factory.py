from twisted.internet.defer import Deferred
from twisted.internet.protocol import Protocol, ReconnectingClientFactory
from twisted.python import log

from txbitcoin.protocols import BitcoinProtocol


class BitcoinClientFactory(ReconnectingClientFactory):
    initialDelay = 0.1
    protocol = BitcoinProtocol
    
    def __init__(self, maxRetries = 2):
        """
        Args:
            maxRetries: The number of times we should try reconnecting before abandoning
                        a connection.
        """
        self.client = None
        self.addr = None
        self.pool = None
        self.deferred = Deferred()
        self.maxRetries = maxRetries

    def buildProtocol(self, addr):
        self.client = self.protocol()
        self.addr = addr
        self.client.factory = self
        # don't do this - some clients cleanly connect and then
        # disconnect, which sets retries to 0 each time, meaning
        # we'd never stop trying
        #self.resetDelay()
        return self.client

    def clientConnectionLost(self, connector, reason):
        log.msg("Lost connection to %s - %s (%i retries)" % (self.addr, reason, self.retries))
        self.client = None
        if self.retries > self.maxRetries:
            self.stopTrying()
            if self.pool is not None:
                self.pool.connectionFailed(self)
        ReconnectingClientFactory.clientConnectionLost(self, connector, reason)

    def clientConnectionFailed(self, connector, reason):
        log.msg("Connection failed to %s - %s (%i retries)" % (self.addr, reason, self.retries))
        self.client = None
        if self.retries > self.maxRetries:
            self.stopTrying()
            if self.pool is not None:
                self.pool.connectionFailed(self)
        ReconnectingClientFactory.clientConnectionFailed(self, connector, reason)

    def connectionMade(self):
        # Only fire deferred after the first connection has been made.
        # This is used in the ConnectedYamClient to keep track of when
        # all factories have connected so that ConnectedYamClient.connect()
        # can return a deferred list of these deferreds.
        log.msg("Connection made to %s" % self.addr)
        if self.deferred is not None:
            self.deferred.callback(self)
            self.deferred = None
