#!/usr/bin/env python3
"""OT#005 probe 1: connect, capture unsolicited bytes, then send real STARTDT act."""
import socket, time, binascii, sys, json

HOST = "169.58.126.107"
PORT = 6004

def hx(b):
    return binascii.hexlify(b).decode()

log = {}

s = socket.socket()
s.settimeout(3)
t0 = time.time()
s.connect((HOST, PORT))
log["connect_time"] = time.time() - t0

# Step 1: see if anything arrives unsolicited within 2s
s.settimeout(2)
try:
    data = s.recv(4096)
    log["unsolicited_banner"] = hx(data)
    log["unsolicited_banner_len"] = len(data)
except socket.timeout:
    log["unsolicited_banner"] = None
    log["unsolicited_banner_len"] = 0

time.sleep(1.2)

# Step 2: send real STARTDT act U-frame: 68 04 07 00 00 00
startdt_act = bytes.fromhex("680407000000")
s.settimeout(3)
s.send(startdt_act)
log["sent_startdt_act"] = hx(startdt_act)
try:
    resp = s.recv(4096)
    log["startdt_response"] = hx(resp)
    log["startdt_response_len"] = len(resp)
except socket.timeout:
    log["startdt_response"] = None
    log["startdt_response_len"] = 0

s.close()

print(json.dumps(log, indent=2))
with open("workspaces/ot-005/artifacts/probe1.log", "w") as f:
    json.dump(log, f, indent=2)
