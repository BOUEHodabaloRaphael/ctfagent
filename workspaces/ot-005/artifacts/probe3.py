#!/usr/bin/env python3
"""OT#005 probe 3: single persistent connection, paced sends (>=1.2s apart):
  1) connect, capture unsolicited bytes
  2) STARTDT act -> expect STARTDT con
  3) General Interrogation (C_IC_NA_1, COT=6, CA=1, QOI=20)
  4) collect and log every APDU that comes back
No reconnects. This is the only network action in this run.
"""
import socket, time, binascii, json

HOST = "169.58.126.107"
PORT = 6004

def hx(b):
    return binascii.hexlify(b).decode()

def build_u(ctrl1):
    return bytes([0x68, 0x04, ctrl1, 0x00, 0x00, 0x00])

def build_i(asdu, tx, rx):
    c1 = (tx << 1) & 0xFF
    c2 = (tx >> 7) & 0xFF
    c3 = (rx << 1) & 0xFF
    c4 = (rx >> 7) & 0xFF
    apci = bytes([0x68, 4 + len(asdu), c1, c2, c3, c4])
    return apci + asdu

def split_apdus(buf):
    frames = []
    i = 0
    while i < len(buf):
        if buf[i] != 0x68:
            i += 1
            continue
        if i + 1 >= len(buf):
            break
        l = buf[i+1]
        if i + 2 + l > len(buf):
            break
        frames.append(buf[i:i+2+l])
        i += 2 + l
    return frames

def drain(s, timeout):
    s.settimeout(timeout)
    buf = b""
    try:
        while True:
            chunk = s.recv(4096)
            if not chunk:
                break
            buf += chunk
    except socket.timeout:
        pass
    return buf

log = {"steps": []}
s = socket.socket()
s.settimeout(5)
t0 = time.time()
s.connect((HOST, PORT))
log["connect_time"] = time.time() - t0

# 1) unsolicited capture
banner = drain(s, 2)
log["steps"].append({"action": "post_connect_capture", "raw": hx(banner), "len": len(banner)})

time.sleep(1.5)

# 2) STARTDT
startdt = build_u(0x07)
s.send(startdt)
log["steps"].append({"action": "send_startdt_act", "frame": hx(startdt)})
r = drain(s, 3)
log["steps"].append({"action": "startdt_response", "raw": hx(r), "len": len(r)})

time.sleep(1.5)

# 3) General Interrogation
tx, rx = 0, 0
asdu = bytes([0x64, 0x01, 0x06, 0x00]) + (1).to_bytes(2, "little") + bytes([0,0,0,20])
frame = build_i(asdu, tx, rx)
s.send(frame)
log["steps"].append({"action": "send_general_interrogation", "frame": hx(frame)})

# 4) collect responses over a few seconds (GI replies can be many I-frames)
resp = drain(s, 6)
apdus = split_apdus(resp)
log["steps"].append({
    "action": "gi_response_raw",
    "raw_len": len(resp),
    "raw": hx(resp),
    "num_apdus": len(apdus),
    "apdus": [hx(a) for a in apdus],
})

s.close()
print(json.dumps(log, indent=2))
with open("workspaces/ot-005/artifacts/probe3.log", "w") as f:
    json.dump(log, f, indent=2)
