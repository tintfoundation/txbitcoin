import sys
import os
sys.path.append(os.path.dirname(__file__))

from twisted.python import log
from twisted.internet import reactor
from txbitcoin.factory import BitcoinClientFactory
from txbitcoin.pool import BitcoinPool

log.startLogging(sys.stdout)

def presult(result):
    for tx in result:
        print tx
    p.disconnect()
    reactor.stop()

def failure(reason):
    print "FAILURE:", reason
    p.disconnect()
    reactor.stop()

def getblocks(pool):
    blocks = ["00000000000000000828203cd2abffe91f5bff604fe9dea423acf85aa0576b79"]
    d = pool.getBlockList(blocks)
    d.addCallbacks(presult, failure)

p = BitcoinPool()
p.bootstrap()
reactor.callLater(3, getblocks, p)
reactor.run()
