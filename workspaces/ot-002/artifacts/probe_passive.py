#!/usr/bin/env python3
"""Step 1: passive connect - see if the service sends a banner/initial state without us writing anything."""
import socket
import sys

HOST = "169.58.126.107"
PORT = 6001

def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(5)
    s.connect((HOST, PORT))
    print(f"[+] Connected to {HOST}:{PORT}")
    try:
        data = s.recv(4096)
        print(f"[+] Received {len(data)} bytes on connect: {data.hex()}")
    except socket.timeout:
        print("[-] No data received within timeout (no banner).")
    s.close()

if __name__ == "__main__":
    main()
