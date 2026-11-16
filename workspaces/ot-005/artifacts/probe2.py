#!/usr/bin/env python3
"""OT#005 probe 2: STARTDT handshake, then General Interrogation (C_IC_NA_1, COT=6)
on CA=1, and listen for all ASDUs returned (GI response is normally many I-frames:
individual point reports + activation confirmation + activation termination)."""
import socket, time, binascii, json, sys

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

def recv_frames(s, total_timeout=4):
    """Collect all APDUs arriving within total_timeout seconds."""
    frames = []
    s.settimeout(total_timeout)
    buf = b""
    end = time.time() + total_timeout
    while time.time() < end:
        try:
            s.settimeout(max(0.2, end - time.time()))
            chunk = s.recv(4096)
            if not chunk:
                break
            buf += chunk
        except socket.timeout:
            break
    # split buf into APDUs by 0x68 start + length byte
    i = 0
    while i < len(buf):
        if buf[i] != 0x68:
            i += 1
            continue
        if i + 1 >= len(buf):
            break
        l = buf[i+1]
        frame = buf[i:i+2+l]
        if len(frame) < 2 + l:
            break  # incomplete, stop
        frames.append(frame)
        i += 2 + l
    return frames, buf

log = {"steps": []}
s = socket.socket()
s.settimeout(5)
s.connect((HOST, PORT))

# STARTDT
s.send(build_u(0x07))
time.sleep(0.3)
r = s.recv(1024)
log["steps"].append({"action": "startdt_act", "response": hx(r)})

time.sleep(1.0)

# General Interrogation: TypeId=100 (0x64), VSQ=1, COT=6, OA=0, CA=1 (LE), IOA=0, QOI=20
ca_candidates = [1]
tx = 0
rx = 0
for ca in ca_candidates:
    asdu = bytes([0x64, 0x01, 0x06, 0x00]) + ca.to_bytes(2, "little") + bytes([0,0,0]) + bytes([20])
    frame = build_i(asdu, tx, rx)
    s.send(frame)
    log["steps"].append({"action": f"GI_sent_CA={ca}", "frame": hx(frame)})
    tx += 1
    time.sleep(0.5)
    frames, raw = recv_frames(s, total_timeout=4)
    log["steps"].append({"action": f"GI_response_CA={ca}", "raw_len": len(raw), "raw": hx(raw), "num_frames": len(frames), "frames": [hx(f) for f in frames]})
    # update rx count = number of I-frames received (to ack properly), tx stays same
    i_frames = [f for f in frames if len(f) >= 6 and (f[2] & 0x01) == 0]
    rx += len(i_frames)
    time.sleep(1.0)

s.close()
print(json.dumps(log, indent=2))
with open("workspaces/ot-005/artifacts/probe2.log", "w") as f:
    json.dump(log, f, indent=2)
