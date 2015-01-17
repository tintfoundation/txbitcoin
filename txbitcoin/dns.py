import socket

from twisted.internet import defer
from twisted.names import client, dns

# Taken from src/chainparams.cpp in the bitcoin C client
SEEDS = [ "dnsseed.bluematt.me", "dnsseed.bitcoin.dashjr.org",
          "seed.bitcoinstats.com", "bitseed.xf2.org" ]


class DNSPeerFinder(object):
    def __init__(self, seeds=None):
        self.seeds = seeds or SEEDS
        self.peers = set()

    def find(self):
        ds = map(client.lookupAddress, self.seeds)
        d = defer.gatherResults(ds)
        return d.addCallback(self._setPeers)

    def _setPeers(self, records):
        addresses = []
        for record in records:
            answers, authority, additional = record
            addresses += answers
            
        for answer in addresses:
            if answer.type == dns.A:
                ip = socket.inet_ntop(socket.AF_INET, answer.payload.address)
                self.peers.add(ip)
        return self.peers

def getPeers():
    return DNSPeerFinder().find()
