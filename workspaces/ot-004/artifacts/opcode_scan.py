#!/usr/bin/env python3
"""Full opcode scan for OT#004, same framing style as OT#002: [op:1][payload:4]."""
import socket, binascii, time

HOST, PORT = "169.58.126.107", 6003

def send_op(op: int, payload: bytes = b"\x00\x00\x00\x00", timeout=4):
    try:
        s = socket.create_connection((HOST, PORT), timeout=timeout)
        s.settimeout(timeout)
        s.sendall(bytes([op]) + payload)
        try:
            data = s.recv(4096)
        except socket.timeout:
            data = b""
        s.close()
        return data
    except Exception as e:
        return f"ERR:{e}".encode()

if __name__ == "__main__":
    results = {}
    for op in range(256):
        data = send_op(op)
        if data and not data.startswith(b"ERR"):
            results[op] = data
        time.sleep(0.03)
    print(f"Responsive opcodes: {len(results)}")
    for op, data in sorted(results.items()):
        print(f"op=0x{op:02x} ({op:3d}) -> {len(data):3d} bytes: {binascii.hexlify(data).decode()}  ascii={data!r}")
