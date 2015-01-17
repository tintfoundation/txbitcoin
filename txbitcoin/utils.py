
def hash_to_int(h):
    return h if isinstance(h, int) else int(h, 16)

def hashes_to_ints(hs):
    return map(hash_to_int, hs)
