#!/usr/bin/env python3
import hashlib
from sha256_ext import length_extend

COMMAND = b"user=guest&action=list&ts=1700000000"
TAG = "7d6b1c096a02b4fdb60aa08bc3377d2ad99a59f8236c96efd4a9e55c2575ed51"
SUFFIX = b"&action=export&target=flag"
SEALED = bytes.fromhex(
    "02ee2b9ccb58fa6eb4cdbf54ee3c0b45f1bb129fceef4f2e4148ec4618db4bd597805cfcfb58cc98a6e9d24ea0f74f27ffd21aed"
)

def xor_repeat(data, key):
    return bytes(d ^ key[i % len(key)] for i, d in enumerate(data))

def key_stream(seed_hex, length):
    """Expand a 32-byte seed hash into a keystream of `length` bytes using
    repeated hashing (seed, seed||counter, ...) -- common CTF 'derive key from
    hash' construction when the sealed payload is longer than 32 bytes."""
    out = b""
    counter = 0
    seed = bytes.fromhex(seed_hex)
    while len(out) < length:
        out += hashlib.sha256(seed + counter.to_bytes(4, "big")).digest()
        counter += 1
    return out[:length]

for secret_len in range(0, 65):
    forged_message, forged_mac = length_extend(TAG, secret_len, COMMAND, SUFFIX)
    # Try 1: TAG itself used directly as repeating XOR key
    pt1 = xor_repeat(SEALED, bytes.fromhex(forged_mac))
    # Try 2: TAG expanded via counter-hash keystream
    pt2 = xor_repeat(SEALED, key_stream(forged_mac, len(SEALED)))
    for label, pt in (("direct-repeat", pt1), ("counter-stream", pt2)):
        if b"NCTF{" in pt:
            print(f"[secret_len={secret_len}] [{label}] FLAG CANDIDATE: {pt}")

print("scan complete")
