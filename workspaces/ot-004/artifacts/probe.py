#!/usr/bin/env python3
"""Black-box probe for OT#004 (OPC-UA-style custom TCP, 169.58.126.107:6003)."""
import socket, binascii, struct, sys, time

HOST, PORT = "169.58.126.107", 6003

def connect():
    s = socket.create_connection((HOST, PORT), timeout=8)
    s.settimeout(5)
    return s

def try_send(label, payload: bytes):
    try:
        s = connect()
        s.sendall(payload)
        try:
            data = s.recv(4096)
        except socket.timeout:
            data = b""
        print(f"--- {label} ---")
        print("sent  :", binascii.hexlify(payload).decode())
        print("recv  :", len(data), "bytes:", binascii.hexlify(data).decode())
        print("ascii :", repr(data[:200]))
        s.close()
        return data
    except Exception as e:
        print(f"--- {label} --- ERROR: {e}")
        return None

if __name__ == "__main__":
    # 1. Real OPC-UA binary Hello message (chunk type 'F', MessageType "HEL")
    endpoint = b"opc.tcp://%s:%d" % (HOST.encode(), PORT)
    hello_body = struct.pack("<IIIII", 0, 65536, 65536, 0, 0) + struct.pack("<I", len(endpoint)) + endpoint
    header = b"HELF" + struct.pack("<I", 8 + len(hello_body))
    try_send("real-opcua-HEL", header + hello_body)

    time.sleep(0.3)
    # 2. Plain ASCII probes
    try_send("ascii-HELLO", b"HELLO\n")
    time.sleep(0.2)
    try_send("ascii-hel", b"HEL\n")
    time.sleep(0.2)

    # 3. Single-byte opcode style like OT#002 (op:1 + payload:4)
    for op in range(6):
        try_send(f"opcode-{op:02x}", bytes([op]) + b"\x00\x00\x00\x00")
        time.sleep(0.1)

    # 4. Empty/newline probe just to see if anything is sent unsolicited
    try_send("empty", b"")
