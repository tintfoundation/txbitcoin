"""
Until protocoin supports getblocks and getheaders, this file will be necessary.
"""
import struct

from protocoin.serializers import Serializer
from protocoin import fields


class BlockLocator(fields.Field):
    """A block locator type used for getblocks and getheaders"""
    datatype = "<I"

    def parse(self, values):
        self.values = values

    def serialize(self):
        bin_data = StringIO()
        for hash_ in self.values:
            for i in range(8):
                pack_data = struct.pack(self.datatype, hash_ & 0xFFFFFFFF)
                bin_data.write(pack_data)
                hash_ >>= 32
        return bin_data.getvalue()


class GetBlocks(object):
    """The getblocks command."""
    command = "getblocks"

    def __init__(self, hashes):
        self.version = fields.PROTOCOL_VERSION
        self.hash_count = len(hashes)
        self.hash_stop = 0
        self.block_hashes = hashes


class GetBlocksSerializer(Serializer):
    model_class = GetBlocks
    version = fields.UInt32LEField()
    hash_count = fields.VariableIntegerField()
    block_hashes = BlockLocator()
    hash_stop = fields.Hash()
