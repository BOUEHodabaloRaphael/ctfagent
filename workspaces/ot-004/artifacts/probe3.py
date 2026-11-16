#!/usr/bin/env python3
"""
Follow-up to probe2.py: the previous connection apparently self-closed after
~22 requests (not idle-timeout related), cutting off the long-Write and
BE-length tests before they ran. Redo those two cleanly on fresh short-lived
connections (few requests each, well under any request-count ceiling).
"""
import socket, struct, binascii, time

HOST, PORT = "169.58.126.107", 6003

def connect():
    s = socket.create_connection((HOST, PORT), timeout=10)
    s.settimeout(6)
    return s

def recv_all_available(s, total_wait=4.0, chunk_timeout=1.0):
    s.settimeout(chunk_timeout)
    buf = b""
    deadline = time.time() + total_wait
    while time.time() < deadline:
        try:
            d = s.recv(4096)
            if not d:
                print("    [closed/EOF]")
                break
            buf += d
        except socket.timeout:
            continue
    return buf

def frame(op, data, length=None, big_endian_len=False):
    if length is None:
        length = len(data)
    fmt = ">I" if big_endian_len else "<I"
    return bytes([op]) + struct.pack(fmt, length) + data

def do(s, label, raw, wait=4.0):
    print(f"\n--- {label} ---")
    print("sent  :", binascii.hexlify(raw).decode())
    s.sendall(raw)
    data = recv_all_available(s, total_wait=wait)
    print("recv  :", len(data), "bytes:", binascii.hexlify(data).decode())
    return data

# --- Fresh connection #1: long Write payload ---
s = connect()
print(f"=== conn1 at {time.ctime()} ===")
do(s, "sanity op1", frame(1, b"\x00\x00\x00\x00"), wait=3.0)
time.sleep(1.5)
long_payload = b"\x55\x00\x00\x00" + (b"\x41" * 36)
do(s, "op4 Write 40-byte payload", frame(4, long_payload), wait=4.0)
time.sleep(1.0)
# immediate follow-up Read on same (possibly-corrupted) nodeid to see any effect
do(s, "op3 Read same nodeid=0x55 after long write", frame(3, b"\x55\x00\x00\x00"), wait=4.0)
try:
    s.close()
except Exception:
    pass

time.sleep(2.0)

# --- Fresh connection #2: len field itself big-endian ---
s2 = connect()
print(f"\n=== conn2 at {time.ctime()} ===")
do(s2, "sanity op1", frame(1, b"\x00\x00\x00\x00"), wait=3.0)
time.sleep(1.5)
do(s2, "op2 Browse len-field BIG-ENDIAN(value=4)", frame(2, b"\x00\x00\x00\x00", big_endian_len=True), wait=5.0)
try:
    s2.close()
except Exception:
    pass

print(f"\n=== done at {time.ctime()} ===")
