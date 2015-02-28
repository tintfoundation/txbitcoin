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


class InsuficientPeers(Exception):
    """
    There aren't enough peers for a consensus.
    """


class FailedConsensus(Exception):
    """
    Peers do not agree on results!
    """


def _callWithConsensus(cmd):
    """
    Call the given command on consensusSize clients.  Ensure the results
    are all the same.  The consensusSize is based on the constructor argument.
    
    Args:
        cmd: The command to call (as a string)
    """
    def func(self, *args, **kwargs):
        clients = self.getClients()
        if len(clients) < self.consensusSize:
            msg = "Only %i peers, not enough for consensus of %i" % (len(clients), self.consensusSize)
            raise InsuficientPeers(msg)
        
        ds = []
        for client in random.sample(clients, self.consensusSize):
            func = getattr(client, cmd)
            ds.append(func(*args, **kwargs))
        return defer.gatherResults(ds).addCallback(_ensureConsensus)
    return func


def _ensureConsensus(results):
    if len(results) == 0:
        return None

    default = results[0]
    if len(results) == 1:
        return default

    for result in results[1:]:
        if result != default:
            msg = "Failed consensus: %s != %s" % (result, default)
            raise FailedConsensus(msg)
    return default


class BitcoinPool(object):
    factory = BitcoinClientFactory
    
    def __init__(self, minsize=5, maxsize=10, consensusSize=5):
        self.minsize = minsize
        self.maxsize = maxsize
        self.consensusSize = consensusSize
        self.peerAddys = deque()
        self.factories = []
        self.blacklist = set()

        #def runEverySecond():
        #    clients = self.getClients()
        #    print "Connected to %i peers" % len(clients), [ c.factory.addr for c in clients ]
        #l = task.LoopingCall(runEverySecond)
        #l.start(1.0)

    def bootstrap(self):
        d = dns.getPeers()
        return d.addCallback(self.connect)

    def getClients(self):
        return [f.client for f in self.factories if f.client is not None]

    def disconnect(self):
        for f in self.factories:
            f.disconnect()

    def connect(self, addys=None):
        """
        Args:
            addys: A list of addresses to connect
                       to as the initial set.  More addys
                       will be found as necessary.
        """        
        if len(self) == self.maxsize:
            return defer.succeed(self)

        for addy in (addys or []):
            if addy not in self.blacklist and addy not in self.peerAddys:
                self.peerAddys.append(addy)

        if not self.peerAddys and len(self.getClients()) < self.minsize:
            raise NoPeersException("Could not find any new peers to connect to.")

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

    def __len__(self):
        return len(self.factories)

    getBlockList = _callWithConsensus('getBlockList')
