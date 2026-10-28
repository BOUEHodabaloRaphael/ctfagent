#!/usr/bin/env python3
"""Empirically search for XXH3-128 differential collision patterns in the
long-input path (len > 240 bytes) using the real xxhash C library as oracle.
No reimplementation of internals needed -- just measure real collision rates.
"""
import os
import random
import xxhash

def xxh128(msg: bytes, seed: int) -> bytes:
    return xxhash.xxh3_128_digest(msg, seed=seed)

def test_pattern(name, make_pair, length, trials=200_000):
    m1, m2 = make_pair(length)
    assert len(m1) == length and len(m2) == length
    assert m1 != m2
    hits = 0
    for _ in range(trials):
        seed = random.getrandbits(64)
        if xxh128(m1, seed) == xxh128(m2, seed):
            hits += 1
    rate = hits / trials
    print(f"[{name}] len={length} hits={hits}/{trials} rate={rate:.2e}")
    return hits

random.seed(1234)
base = os.urandom(1024)

def flip_lane(length, lane_byte_offset):
    m1 = bytearray(base[:length])
    m2 = bytearray(m1)
    for k in range(8):
        m2[lane_byte_offset + k] ^= 0xFF
    return bytes(m1), bytes(m2)

def flip_two_complementary(length, off):
    # w1 = ~w0 trick adapted: set chunk at off..off+16, then complement both halves in m2
    m1 = bytearray(base[:length])
    w0 = bytes(m1[off:off+8])
    w1 = bytes((b ^ 0xFF) for b in w0)
    m1[off:off+8] = w0
    m1[off+8:off+16] = w1
    m2 = bytearray(m1)
    for k in range(16):
        m2[off+k] ^= 0xFF
    return bytes(m1), bytes(m2)

print("=== single-lane flips at various offsets, len=256 ===")
for off in [0, 8, 16, 64, 128, 192, 248]:
    test_pattern(f"single-lane@{off}", lambda L, off=off: flip_lane(L, off), 256, trials=100_000)

print("=== mix16B-style complementary pair at various offsets, len=256 ===")
for off in [0, 8, 16, 64, 128, 192, 240]:
    test_pattern(f"compl-pair@{off}", lambda L, off=off: flip_two_complementary(L, off), 256, trials=100_000)

print("=== same tests at len=512 ===")
for off in [0, 64, 256, 496]:
    test_pattern(f"single-lane@{off}", lambda L, off=off: flip_lane(L, off), 512, trials=50_000)
for off in [0, 64, 256, 480]:
    test_pattern(f"compl-pair@{off}", lambda L, off=off: flip_two_complementary(L, off), 512, trials=50_000)
