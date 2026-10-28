#!/usr/bin/env python3
"""OT#002 - Aurora-style out-of-phase reclose trigger.
Opens breaker (implicit by not closing), watches grid/generator phase
differential, closes exactly at peak anti-phase (~180 deg), then polls
post-event telemetry for status/flag changes.
"""
import socket
import struct
import sys
import time

HOST, PORT = "169.58.126.107", 6001


def send_recv(s, frame, timeout=5):
    s.settimeout(timeout)
    s.sendall(frame)
    try:
        return s.recv(4096)
    except socket.timeout:
        return b"<TIMEOUT>"


def norm(d):
    d = d % 360
    if d > 180:
        d -= 360
    return d


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((HOST, PORT))

    t0 = time.time()
    triggered = False
    post_samples = 0
    max_post_samples = 15

    for i in range(400):
        resp = send_recv(s, bytes([1, 0, 0, 0, 0]))
        if len(resp) != 11:
            print(f"non-11-byte telemetry: {resp.hex()} len={len(resp)}", flush=True)
            continue
        status = resp[0]
        f1 = struct.unpack("<f", resp[1:5])[0]
        f2 = struct.unpack("<f", resp[5:9])[0]
        trailer = resp[9:11]
        d = norm(f1 - f2)

        if not triggered:
            if abs(d) > 175:
                t = time.time() - t0
                print(f">>> TRIGGER t={t:.2f}s diff={d:.2f} - sending CLOSE", flush=True)
                close_resp = send_recv(s, bytes([3, 0, 0, 0, 0]))
                print(f"CLOSE resp: {close_resp.hex()}", flush=True)
                triggered = True
            else:
                if i % 5 == 0:
                    print(f"t={time.time()-t0:6.2f}s diff={d:+7.2f} (waiting)", flush=True)
        else:
            post_samples += 1
            print(
                f"POST#{post_samples} t={time.time()-t0:6.2f}s status={status:02x} "
                f"f1={f1:.3f} f2={f2:.3f} trailer={trailer.hex()} raw={resp.hex()}",
                flush=True,
            )
            if status != 0:
                print("*** STATUS BYTE NONZERO - possible destroyed/flag state ***", flush=True)
            if post_samples >= max_post_samples:
                break
        time.sleep(0.15)

    s.close()


if __name__ == "__main__":
    main()
