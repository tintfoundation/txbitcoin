import socket
import random

from twisted.internet import defer
from twisted.names import client, dns

# Taken from src/chainparams.cpp in the bitcoin C client
SEEDS = [ "dnsseed.bluematt.me", "dnsseed.bitcoin.dashjr.org",
          "seed.bitcoinstats.com", "bitseed.xf2.org" ]


def _parsePeers(records):
    addresses = []
    for record in records:
        answers, authority, additional = record
        addresses += answers

    peers = set()
    for answer in addresses:
        if answer.type == dns.A:
            ip = socket.inet_ntop(socket.AF_INET, answer.payload.address)
            peers.add(ip)

    # shake it up!  This means our list will change on each call
    peers = list(peers)
    random.shuffle(peers)
    print peers
    return peers


def getPeers(seeds=None):
    ds = map(client.lookupAddress, seeds or SEEDS)
    d = defer.gatherResults(ds)
    return d.addCallback(_parsePeers)
