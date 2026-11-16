#!/usr/bin/env python3
"""
OT#004 round 2 — single persistent connection, paced requests, testing the
"not yet tested" and "genuinely new" theories listed in notes.md:
  1. len field itself big-endian (op2)
  2. structured OPC-UA string NodeId encoding (type=0x03, ns:2LE, len:4LE, utf8) for Browse/Read
  3. patient multi-recv wait (10-15s) after Browse, outside any cooldown
  4. Browse with len=0 (true zero-length payload, not 4 zero bytes)
  5. pagination/continuation-point theory: resend prior Browse response payload as next Browse data
  6. Read with AttributeId-only 1-byte payload right after a Browse (implicit "current node" theory)
  7. Write with a long (40-byte) payload (parser overflow / path divergence)
  8. Deliberate bad framing: len field > actual bytes sent, then complete it after a short wait

All on ONE persistent TCP connection, with ~1.5-2s sleep between distinct
requests (never reconnecting mid-sequence except the final bad-framing test
which is terminal for the connection by design).
"""
import socket, struct, binascii, time, sys

HOST, PORT = "169.58.126.107", 6003
LOG = []

def log(line):
    print(line)
    LOG.append(line)

def connect():
    s = socket.create_connection((HOST, PORT), timeout=10)
    s.settimeout(6)
    return s

def recv_all_available(s, total_wait=3.0, chunk_timeout=1.0):
    """Collect bytes over a window, doing multiple recv() calls."""
    s.settimeout(chunk_timeout)
    buf = b""
    deadline = time.time() + total_wait
    while time.time() < deadline:
        try:
            d = s.recv(4096)
            if not d:
                log("    [recv_all_available] connection closed (EOF)")
                break
            buf += d
        except socket.timeout:
            continue
    return buf

def frame(op, data: bytes, length=None, big_endian_len=False):
    if length is None:
        length = len(data)
    fmt = ">I" if big_endian_len else "<I"
    return bytes([op]) + struct.pack(fmt, length) + data

def do(s, label, raw_bytes, wait=1.0, recv_window=3.0):
    log(f"\n--- {label} ---")
    log(f"sent  : {binascii.hexlify(raw_bytes).decode()}")
    s.sendall(raw_bytes)
    data = recv_all_available(s, total_wait=recv_window, chunk_timeout=1.0)
    log(f"recv  : {len(data)} bytes: {binascii.hexlify(data).decode()}")
    if len(data) >= 5:
        resp_op = data[0]
        rlen = struct.unpack("<I", data[1:5])[0]
        payload = data[5:5+rlen]
        log(f"parsed: resp_op=0x{resp_op:02x} len={rlen} payload={binascii.hexlify(payload).decode()}")
    time.sleep(wait)
    return data

def main():
    s = connect()
    log(f"=== connected to {HOST}:{PORT} at {time.ctime()} ===")

    # 0. Sanity: op=1 Hello baseline (confirm no cooldown / server alive)
    do(s, "0. sanity op1 Hello", frame(1, b"\x00\x00\x00\x00"))

    # 0b. Sanity: canon Browse baseline, reconfirm unchanged
    do(s, "0b. sanity op2 Browse canon(4 zero bytes)", frame(2, b"\x00\x00\x00\x00"))

    # 4. Browse with TRUE len=0 (empty data, not 4 zero bytes)
    r_len0 = do(s, "4. op2 Browse len=0 (truly empty)", frame(2, b""))

    # 5. Pagination/continuation theory: resend prior canon Browse response
    #    payload bytes (00 00 00 00 04) as the NEXT Browse request's data.
    cont_payload = bytes.fromhex("0000000004")
    do(s, "5. op2 Browse with prior response payload as continuation cursor",
       frame(2, cont_payload))

    # 6. Read with AttributeId-ONLY 1-byte payloads, right after a Browse,
    #    testing "current node is implicit session state from last Browse".
    do(s, "6pre. op2 Browse (root) to set 'current node' before attr-only Read",
       frame(2, b"\x00\x00\x00\x00"))
    for attr_id, name in [(1, "NodeId"), (2, "NodeClass"), (3, "BrowseName"),
                           (4, "DisplayName"), (13, "Value")]:
        do(s, f"6. op3 Read AttributeId-only ({attr_id}={name})",
           frame(3, bytes([attr_id])))

    # 2. Structured OPC-UA string NodeId encoding:
    #    [identifierType=0x03][namespaceIndex:2 LE][length:4 LE][utf8 bytes]
    def string_nodeid(ns, s_):
        b = s_.encode()
        return bytes([0x03]) + struct.pack("<H", ns) + struct.pack("<I", len(b)) + b

    for name in ["Objects", "SafetySystem", "ReactorController", "SIS", "Enabled"]:
        for ns in (0, 1):
            payload = string_nodeid(ns, name)
            do(s, f"2. op2 Browse structured-string-NodeId ns={ns} '{name}'",
               frame(2, payload), wait=1.2)

    # also try as Read argument on the most plausible one
    do(s, "2b. op3 Read structured-string-NodeId ns=1 'Enabled'",
       frame(3, string_nodeid(1, "Enabled")))

    # 3. Patient multi-recv wait after a fresh Browse (10-15s), outside cooldown,
    #    clean retry of the earlier polluted test.
    log("\n--- 3. patient wait after Browse (15s, multi-recv) ---")
    raw = frame(2, b"\x00\x00\x00\x00")
    log(f"sent  : {binascii.hexlify(raw).decode()}")
    s.sendall(raw)
    data = recv_all_available(s, total_wait=15.0, chunk_timeout=2.0)
    log(f"recv over 15s: {len(data)} bytes: {binascii.hexlify(data).decode()}")
    time.sleep(1.5)

    # 7. Write with a long (40-byte) payload -- overflow / path divergence probe
    long_payload = b"\x55\x00\x00\x00" + (b"\x41" * 36)  # fake nodeid=0x55 + 36 'A's
    do(s, "7. op4 Write long (40-byte) payload", frame(4, long_payload), wait=1.5)

    # 1. len field itself encoded BIG-ENDIAN (not just content endianness)
    #    Expect: if server truly parses len as LE always, BE-encoded len=4
    #    (bytes 00 00 00 04) will be read as a huge length -> hang/no-response.
    #    We give it a short recv window and do NOT block long if it stalls.
    log("\n--- 1. op2 Browse with len field itself BIG-ENDIAN (value=4) ---")
    raw = frame(2, b"\x00\x00\x00\x00", big_endian_len=True)
    log(f"sent  : {binascii.hexlify(raw).decode()}")
    s.sendall(raw)
    data = recv_all_available(s, total_wait=3.0, chunk_timeout=1.0)
    log(f"recv  : {len(data)} bytes: {binascii.hexlify(data).decode()}")

    # If that desynced the stream (server now expects 0x04000000 bytes), we
    # must not keep reusing this connection -- reconnect cleanly for the last
    # (intentionally desync-y) test.
    try:
        s.close()
    except Exception:
        pass
    time.sleep(2.0)

    # 8. Deliberate bad framing: len field claims MORE than bytes actually
    #    sent, wait briefly, then complete the frame -- see if a one-shot
    #    different behavior appears before server just buffers/hangs.
    s2 = connect()
    log(f"\n=== reconnected for test 8 at {time.ctime()} ===")
    op = 2
    claimed_len = 20
    actual_data = b"\x00\x00\x00\x00"  # only 4 of the claimed 20 bytes
    header = bytes([op]) + struct.pack("<I", claimed_len)
    log(f"--- 8. op2 Browse: header claims len=20, sending only 4 bytes now ---")
    log(f"sent-partial: {binascii.hexlify(header + actual_data).decode()}")
    s2.sendall(header + actual_data)
    # peek for any early/unexpected response before completing the frame
    early = recv_all_available(s2, total_wait=2.0, chunk_timeout=1.0)
    log(f"recv-before-completion: {len(early)} bytes: {binascii.hexlify(early).decode()}")
    # now complete the frame with the remaining 16 bytes
    remainder = b"\x00" * 16
    log(f"sent-remainder: {binascii.hexlify(remainder).decode()}")
    s2.sendall(remainder)
    final = recv_all_available(s2, total_wait=4.0, chunk_timeout=1.0)
    log(f"recv-after-completion: {len(final)} bytes: {binascii.hexlify(final).decode()}")

    try:
        s2.close()
    except Exception:
        pass

    log(f"\n=== done at {time.ctime()} ===")

if __name__ == "__main__":
    main()
    with open("/home/kali/ctfagent/workspaces/ot-004/artifacts/probe2.log", "w") as f:
        f.write("\n".join(LOG) + "\n")
