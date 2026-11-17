#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NCTF26 — fausse colline KoTH pour tester le kit SANS reseau (self-test offline).

Sert un mini-scorer qui imite le modele annonce : un "roi" courant, des claims,
un status JSON. Utilise par `bash koth_hold.sh selftest` :
  1. demarre cette colline sur 127.0.0.1:<port> ;
  2. lance hold_hill.py --probe contre elle (1 claim + 1 status) ;
  3. lance une tenue courte et verifie que ROI(nous)=True tient face a un rival ;
  4. verifie que STOP arrete bien la tenue.

Aucune dependance, aucun acces externe.

  python3 mock_hill.py --port 18777 [--rival] [--rival-interval 1.5]
"""
import argparse
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

STATE = {"king": None, "claims": 0, "by": {}, "log": []}
LOCK = threading.Lock()
TEAM = "TEAM-US"
RIVAL = "TEAM-RIVAL"
ARGS = None


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def _send(self, code, payload):
        raw = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def _who(self):
        body = b""
        n = int(self.headers.get("Content-Length") or 0)
        if n:
            body = self.rfile.read(n)
        team = None
        if body:
            try:
                j = json.loads(body)
                for k in ("team", "team_code", "token", "id"):
                    if isinstance(j, dict) and j.get(k):
                        team = str(j[k])
                        break
            except Exception:
                team = body.decode("utf-8", "replace").strip()[:64] or None
        return team or self.headers.get("X-Team") or "anonymous"

    def do_POST(self):
        if self.path.startswith("/claim"):
            team = self._who()
            with LOCK:
                STATE["claims"] += 1
                STATE["by"][team] = STATE["by"].get(team, 0) + 1
                STATE["king"] = team
                STATE["log"].append((time.time(), team))
                del STATE["log"][:-200]
            return self._send(200, {"ok": True, "king": team, "claims": STATE["claims"]})
        return self._send(404, {"error": "no such route"})

    def do_GET(self):
        if self.path.startswith("/status"):
            with LOCK:
                return self._send(200, {"king": STATE["king"], "claims": STATE["claims"],
                                        "by": dict(STATE["by"])})
        if self.path.startswith("/health"):
            return self._send(200, {"ok": True})
        return self._send(404, {"error": "no such route"})

    def log_message(self, *a):
        pass


def rival_loop(interval):
    while True:
        time.sleep(interval)
        with LOCK:
            STATE["claims"] += 1
            STATE["by"][RIVAL] = STATE["by"].get(RIVAL, 0) + 1
            STATE["king"] = RIVAL


def main():
    global ARGS
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=18777)
    ap.add_argument("--rival", action="store_true")
    ap.add_argument("--rival-interval", type=float, default=1.5)
    ARGS = ap.parse_args()
    if ARGS.rival:
        threading.Thread(target=rival_loop, args=(ARGS.rival_interval,), daemon=True).start()
    srv = ThreadingHTTPServer(("127.0.0.1", ARGS.port), Handler)
    print("mock_hill on 127.0.0.1:%d rival=%s" % (ARGS.port, ARGS.rival), flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
