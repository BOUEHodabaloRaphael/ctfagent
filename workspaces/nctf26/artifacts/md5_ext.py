#!/usr/bin/env python3
"""MD5 length-extension: forge MD5(secret||known_msg||glue||extra) knowing
only MD5(secret||known_msg) and (bruteforced) len(secret)."""
import struct

def leftrotate(x, c):
    return ((x << c) | (x >> (32 - c))) & 0xFFFFFFFF

S = [7,12,17,22]*4 + [5,9,14,20]*4 + [4,11,16,23]*4 + [6,10,15,21]*4
K = [int(abs(__import__('math').sin(i+1)) * 2**32) & 0xFFFFFFFF for i in range(64)]

def md5_padding(msg_len):
    ml_bits = (msg_len * 8) & 0xFFFFFFFFFFFFFFFF
    pad = b'\x80'
    pad_len = (56 - (msg_len + 1) % 64) % 64
    pad += b'\x00' * pad_len
    pad += struct.pack('<Q', ml_bits)
    return pad

def md5_compress(state, block):
    a0, b0, c0, d0 = state
    M = list(struct.unpack('<16I', block))
    A, B, C, D = a0, b0, c0, d0
    for i in range(64):
        if i < 16:
            F = (B & C) | (~B & D)
            g = i
        elif i < 32:
            F = (D & B) | (~D & C)
            g = (5*i + 1) % 16
        elif i < 48:
            F = B ^ C ^ D
            g = (3*i + 5) % 16
        else:
            F = C ^ (B | (~D & 0xFFFFFFFF))
            g = (7*i) % 16
        F = (F + A + K[i] + M[g]) & 0xFFFFFFFF
        A = D
        D = C
        C = B
        B = (B + leftrotate(F, S[i])) & 0xFFFFFFFF
    return [
        (a0+A) & 0xFFFFFFFF, (b0+B) & 0xFFFFFFFF,
        (c0+C) & 0xFFFFFFFF, (d0+D) & 0xFFFFFFFF,
    ]

def state_from_hex(h):
    raw = bytes.fromhex(h)
    return list(struct.unpack('<4I', raw))

def hex_from_state(state):
    return struct.pack('<4I', *state).hex()

def length_extend(known_mac_hex, secret_len, known_message, extra_data):
    total_known_len = secret_len + len(known_message)
    glue = md5_padding(total_known_len)
    state = state_from_hex(known_mac_hex)
    total_len_before_extra = total_known_len + len(glue)
    data = extra_data + md5_padding(total_len_before_extra + len(extra_data))
    for i in range(0, len(data), 64):
        state = md5_compress(state, data[i:i+64])
    forged_mac = hex_from_state(state)
    forged_message = known_message + glue + extra_data
    return forged_message, forged_mac

if __name__ == '__main__':
    import hashlib
    secret = b'topsecretkey123'
    msg = b'user=guest'
    extra = b'&user=admin'
    real = hashlib.md5(secret+msg).hexdigest()
    fm, fmac = length_extend(real, len(secret), msg, extra)
    expected = hashlib.md5(secret+fm).hexdigest()
    assert fmac == expected
    print('self-test OK')
