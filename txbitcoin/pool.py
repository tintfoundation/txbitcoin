import random
from collections import deque

from twisted.internet import reactor, defer, task
from twisted.python import log

from txbitcoin.factory import BitcoinClientFactory
from txbitcoin import dns


class NoPeersException(Exception):
    """
    No more peers to connect to!
    """


class BitcoinPool(object):
    factory = BitcoinClientFactory
    
    def __init__(self, maxsize=10):
        self.maxsize = maxsize
        self.peerAddys = deque()
        self.factories = []
        self.blacklist = set()

        #def runEverySecond():
        #    print "Connected to", [ c.factory.addr for c in self.getClients() ]
        #l = task.LoopingCall(runEverySecond)
        #l.start(1.0)

    def bootstrap(self):
        d = dns.getPeers()
        return d.addCallback(self.connect)

    def getClients(self):
        return [f.client for f in self.factories if f.client is not None]

    def connect(self, addys=None):
        """
        Args:
            bootAddys: A list of addresses to connect
                       to as the initial set.  More addys
                       will be found as necessary.
        """
        if len(self) == self.maxsize:
            return defer.succeed(self)

        for addy in (addys or []):
            if addy not in self.blacklist and addy not in self.peerAddys:
                self.peerAddys.append(addy)

        if not self.peerAddys and len(self.getClients()) == 0:
            raise NoPeersException("Could not find any peers to connect to.")

        if not self.peerAddys:
            return self.getPeers().addCallback(self.connect)

        ds = []
        while len(self) < self.maxsize and self.peerAddys:
            addy = self.peerAddys.popleft()
            log.msg("Establishing a connection in pool to %s" % addy)
            factory = self.factory()
            factory.pool = self
            self.factories.append(factory)
            reactor.connectTCP(addy, 8333, factory)
            ds.append(factory.deferred)

        # return self after first connection is made
        d = defer.DeferredList(ds, fireOnOneCallback=True)
        if len(self) < self.maxsize:
            d.addCallback(lambda _: self.getPeers()).addCallbacks(self.connect)
        return d.addCallback(lambda _: self)

    def connectionFailed(self, factory):
        log.msg("Connection to %s failed, creating new connection" % factory.addr)
        self.blacklist.add(factory.addr)
        self.factories.remove(factory)
        
        # now get next addy, calling getaddr on a client if necessary
        if not self.peerAddys:
            return self.getPeers().addCallback(self.connect)
        return self.connect()

    def getPeers(self):
        def extractIPs(addrs):
            ips = [addr.ip_address for addr in addrs]
            return ips

        connected = self.getClients()
        if not connected:
            raise NoPeersException("No peers left to connect to")

        client = random.choice(connected)
        d = client.getPeers()
        d.addCallback(extractIPs)
        return d.addErrback(lambda _: [])

    def getMemPool(self):
        def mp(_):
            client = random.choice(self.getClients())
            return client.getMemPool()
        return self.connect().addCallback(mp)

    def __len__(self):
        return len(self.factories)
