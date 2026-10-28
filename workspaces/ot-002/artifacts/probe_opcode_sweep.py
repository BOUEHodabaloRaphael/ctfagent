#!/usr/bin/env python3
"""Step 2: fuzz opcode byte 0 (0x00-0xFF) with neutral payload (zeros) on remaining 4 bytes.
Fresh connection per opcode to avoid cross-contamination of server-side state.
Logs full hex dump of request/response plus response length and connection behavior (closed vs stays open)."""
import socket
import sys
import time

HOST = "169.58.126.107"
PORT = 6001
TIMEOUT = 2.5

def probe(opcode):
    payload = bytes([opcode, 0, 0, 0, 0])
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(TIMEOUT)
    try:
        s.connect((HOST, PORT))
    except Exception as e:
        return {"opcode": opcode, "error": f"connect failed: {e}"}
    try:
        s.sendall(payload)
    except Exception as e:
        s.close()
        return {"opcode": opcode, "error": f"send failed: {e}"}
    resp = b""
    closed = False
    try:
        while True:
            chunk = s.recv(4096)
            if not chunk:
                closed = True
                break
            resp += chunk
            if len(resp) > 0:
                # try one more quick read to catch multi-packet responses, but don't block forever
                s.settimeout(0.4)
                try:
                    more = s.recv(4096)
                    if more:
                        resp += more
                    else:
                        closed = True
                        break
                except socket.timeout:
                    break
    except socket.timeout:
        pass
    except Exception as e:
        s.close()
        return {"opcode": opcode, "payload": payload.hex(), "resp": resp.hex(), "error": str(e)}
    s.close()
    return {"opcode": opcode, "payload": payload.hex(), "resp": resp.hex(), "resp_len": len(resp), "closed_by_server": closed}

def main():
    results = []
    for opcode in range(256):
        r = probe(opcode)
        results.append(r)
        tag = f"op=0x{opcode:02x}"
        if "error" in r:
            print(f"{tag} payload={r.get('payload','?')} ERROR={r['error']}")
        else:
            print(f"{tag} payload={r['payload']} resp={r['resp']} len={r['resp_len']} closed={r['closed_by_server']}")
        time.sleep(0.02)
    return results

if __name__ == "__main__":
    main()
