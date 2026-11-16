#!/usr/bin/env python3
"""SHA-256 length-extension attack, from-scratch compression function.
Used to forge SHA256(secret || COMMAND || glue_padding || SUFFIX) without
knowing `secret`, only needing its length (bruteforced).
"""
import struct

K = [
    0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
    0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
    0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
    0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
    0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
    0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
    0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
    0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2,
]

MASK = 0xFFFFFFFF

def rotr(x, n):
    return ((x >> n) | (x << (32 - n))) & MASK

def sha256_padding(msg_len):
    """Standard SHA-256 padding for a message of msg_len bytes."""
    ml_bits = msg_len * 8
    pad = b"\x80"
    pad_len = (56 - (msg_len + 1) % 64) % 64
    pad += b"\x00" * pad_len
    pad += struct.pack(">Q", ml_bits)
    return pad

def sha256_compress(state, block):
    """One SHA-256 compression round on a 64-byte block, given 8x32bit state."""
    w = list(struct.unpack(">16I", block))
    for i in range(16, 64):
        s0 = rotr(w[i-15], 7) ^ rotr(w[i-15], 18) ^ (w[i-15] >> 3)
        s1 = rotr(w[i-2], 17) ^ rotr(w[i-2], 19) ^ (w[i-2] >> 10)
        w.append((w[i-16] + s0 + w[i-7] + s1) & MASK)

    a, b, c, d, e, f, g, h = state
    for i in range(64):
        S1 = rotr(e, 6) ^ rotr(e, 11) ^ rotr(e, 25)
        ch = (e & f) ^ (~e & g)
        temp1 = (h + S1 + ch + K[i] + w[i]) & MASK
        S0 = rotr(a, 2) ^ rotr(a, 13) ^ rotr(a, 22)
        maj = (a & b) ^ (a & c) ^ (b & c)
        temp2 = (S0 + maj) & MASK

        h = g; g = f; f = e
        e = (d + temp1) & MASK
        d = c; c = b; b = a
        a = (temp1 + temp2) & MASK

    return [
        (state[0] + a) & MASK, (state[1] + b) & MASK, (state[2] + c) & MASK, (state[3] + d) & MASK,
        (state[4] + e) & MASK, (state[5] + f) & MASK, (state[6] + g) & MASK, (state[7] + h) & MASK,
    ]

def state_from_digest(digest_hex):
    raw = bytes.fromhex(digest_hex)
    return list(struct.unpack(">8I", raw))

def digest_from_state(state):
    return b"".join(struct.pack(">I", x) for x in state).hex()

def length_extend(known_mac_hex, secret_len, known_message, extra_data):
    """Return (forged_message_bytes_without_secret, forged_mac_hex).
    forged_message_bytes_without_secret = known_message + glue_padding + extra_data
    (the part the attacker controls / sends; `secret` itself is never known)."""
    total_known_len = secret_len + len(known_message)
    glue = sha256_padding(total_known_len)

    state = state_from_digest(known_mac_hex)
    # total length so far for extra_data's own final padding
    total_len_before_extra = total_known_len + len(glue)

    # process extra_data in 64-byte blocks, resuming from `state`
    data = extra_data + sha256_padding(total_len_before_extra + len(extra_data))
    for i in range(0, len(data), 64):
        block = data[i:i+64]
        state = sha256_compress(state, block)

    forged_mac = digest_from_state(state)
    forged_message = known_message + glue + extra_data
    return forged_message, forged_mac


if __name__ == "__main__":
    # self-test against hashlib
    import hashlib
    secret = b"supersecretkey12"  # 16 bytes, arbitrary for self-test
    known_message = b"user=guest&action=list&ts=1700000000"
    extra = b"&action=export&target=flag"

    real_mac = hashlib.sha256(secret + known_message).hexdigest()
    forged_msg, forged_mac = length_extend(real_mac, len(secret), known_message, extra)
    expected = hashlib.sha256(secret + forged_msg).hexdigest()
    print("forged_mac  :", forged_mac)
    print("expected mac:", expected)
    assert forged_mac == expected, "length extension implementation BROKEN"
    print("self-test OK: length extension matches hashlib for known secret length")
