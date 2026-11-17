#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NCTF26 — colline MOCK ADVERSARIALE pour prouver l'endurcissement du kit.

Contrairement a une colline gentille a cadence fixe, celle-ci modelise ce qui
casse vraiment un teneur en finale :
  - un rival AGRESSIF qui adapte sa cadence et vise les creneaux du scorer ;
  - des 429/503 aleatoires (rate-limit de la plateforme) avec Retry-After ;
  - des RESETS de conteneur : le roi repasse a "none" et l'etat est efface ;
  - des claims rejetes (400) si le body est vide/malforme.

But : lancer `hill_hold.py` contre elle et verifier que le teneur
  1) remonte au niveau max quand le rival gagne,
  2) redescend quand il tient,
  3) se remet d'un reset sans redemarrer,
  4) ne depasse jamais le plafond de debit (pas de DoS).

  python3 mock_rival.py --port 18800 --aggression 3 [--reset-every 25] [--ratelimit 0.05]

Endpoints :
  POST /claim   {"team": "..."}      -> 200 {ok,king} | 429 | 400
  GET  /status                        -> {king, claims, by, resets, level_estimate}
  GET  /health                        -> {ok}
"""
import argparse
import json
import random
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

STATE = {
    "king": None,
    "score_king": None,
    "claims": 0,
    "by": {},
    "resets": 0,
    "rejected": 0,
    "throttled": 0,
    "since_reset": time.time(),
    "history": [],
    "ticks": 0,
    "score_us": 0,
    "score_rival": 0,
    "score_log": [],
    "last": None,
}
LOCK = threading.Lock()
ARGS = None
RIVAL = "TEAM-RIVAL"


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    # ------------------------------------------------------------------ utils
    def _send(self, code, payload, extra_headers=None):
        raw = json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        for k, v in (extra_headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(raw)

    def _body(self):
        n = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(n) if n else b""
        if not raw:
            return None, raw
        try:
            return json.loads(raw), raw
        except Exception:
            return None, raw

    def _team(self, j, raw):
        if isinstance(j, dict):
            for k in ("team", "team_code", "token", "id"):
                if j.get(k):
                    return str(j[k])
        txt = raw.decode("utf-8", "replace").strip()
        return txt[:64] or None

    # ----------------------------------------------------------------- routes
    def do_POST(self):
        if self.path.startswith("/reset"):
            with LOCK:
                STATE.update({"score_us": 0, "score_rival": 0, "ticks": 0,
                              "score_log": [],
    "last": None, "claims": 0, "by": {},
                              "throttled": 0, "rejected": 0, "resets": 0})
            return self._send(200, {"ok": True, "reset": True})
        if not self.path.startswith("/claim"):
            return self._send(404, {"error": "no such route"})
        j, raw = self._body()
        team = self._team(j, raw)
        if not team:
            with LOCK:
                STATE["rejected"] += 1
            return self._send(400, {"error": "empty claim"})

        # rate-limit aleatoire (la plateforme nous freine)
        if random.random() < ARGS.ratelimit:
            ra = random.choice([1, 2, 3])
            with LOCK:
                STATE["throttled"] += 1
            return self._send(429, {"error": "slow down"}, {"Retry-After": str(ra)})

        with LOCK:
            STATE["claims"] += 1
            STATE["by"][team] = STATE["by"].get(team, 0) + 1
            STATE["king"] = team
            STATE["last"] = (time.time(), team)
            STATE["history"].append((round(time.time(), 2), team))
            del STATE["history"][:-400]
            king = STATE["king"]
        return self._send(200, {"ok": True, "king": king, "claims": STATE["claims"]})

    def do_GET(self):
        if self.path.startswith("/status"):
            with LOCK:
                snap = {
                    "king": STATE["king"],
                    "score_king": STATE["score_king"],
                    "claims": STATE["claims"],
                    "by": dict(STATE["by"]),
                    "resets": STATE["resets"],
                    "ticks": STATE["ticks"],
                    "score_us": STATE["score_us"],
                    "score_rival": STATE["score_rival"],
                    "score_log": STATE["score_log"][-40:],
                    "rejected": STATE["rejected"],
                    "throttled": STATE["throttled"],
                    "since_reset_s": round(time.time() - STATE["since_reset"], 1),
                }
            return self._send(200, snap)
        if self.path.startswith("/health"):
            return self._send(200, {"ok": True})
        return self._send(404, {"error": "no such route"})

    def log_message(self, *a):
        pass


# --------------------------------------------------------------------- rival
def rival_loop():
    """Rival adaptatif : plus il perd, plus il pousse (comme un vrai bot)."""
    rnd = random.Random(1337)
    level = 0
    last_king = None
    while True:
        with LOCK:
            king = STATE["king"]
            lvl_target = 1 if king != RIVAL else 0
        if king == RIVAL and last_king == RIVAL:
            level = max(0, level - 1)
        else:
            level = min(ARGS.aggression, level + 1)
        last_king = king
        # cadence du rival : fixe si demandee, sinon 1.2s au repos -> plancher au max
        interval = ARGS.rival_interval if ARGS.rival_interval > 0 else max(ARGS.rival_min, 1.2 / (1 + level))
        time.sleep(interval * (0.7 + 0.6 * rnd.random()))
        with LOCK:
            STATE["claims"] += 1
            STATE["by"][RIVAL] = STATE["by"].get(RIVAL, 0) + 1
            STATE["king"] = RIVAL
            STATE["last"] = (time.time(), RIVAL)
            STATE["history"].append((round(time.time(), 2), RIVAL))
            del STATE["history"][:-400]


# --------------------------------------------------------------------- reset
def reset_loop():
    """Reset de conteneur : le roi est efface, comme apres une reinitialisation."""
    while True:
        time.sleep(ARGS.reset_every * (0.7 + 0.6 * random.random()))
        with LOCK:
            STATE["king"] = None
            STATE["score_king"] = None
            STATE["resets"] += 1
            STATE["since_reset"] = time.time()
        print("[mock_rival] RESET #%d (king efface)" % STATE["resets"], flush=True)


# ---------------------------------------------------------------------- tick
def tick_loop(period):
    """Scorer realiste : la valeur qui COMPTE est echantillonnee au tick, pas en continu.
    C'est exactement pour ca que le sniping (dernier claim avant le tick) gagne."""
    while True:
        nxt = (int(time.time() // period) + 1) * period
        time.sleep(max(0.0, nxt - time.time()))
        with LOCK:
            STATE["score_king"] = STATE["king"]
            STATE["ticks"] += 1
            if STATE["king"] == "TEAM-US":
                STATE["score_us"] += 1
            elif STATE["king"] == RIVAL:
                STATE["score_rival"] += 1
            lt, lteam = STATE["last"] if STATE["last"] else (0, None)
            STATE["score_log"].append({"t": round(nxt, 3), "king": STATE["score_king"],
                                       "last_team": lteam,
                                       "last_ms": round((time.time() - lt) * 1000, 1)})
            del STATE["score_log"][:-500]
            king, n = STATE["score_king"], STATE["ticks"]
        print("[mock_rival] tick #%d -> roi=%s (dernier claim: %s, il y a %.0f ms)"
              % (n, king, STATE["score_log"][-1]["last_team"],
                 STATE["score_log"][-1]["last_ms"]), flush=True)


def main():
    global ARGS
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=18800)
    ap.add_argument("--aggression", type=int, default=3, help="0=passif 3=tres agressif")
    ap.add_argument("--reset-every", type=float, default=0, help="0 = jamais")
    ap.add_argument("--ratelimit", type=float, default=0.03, help="probabilite de 429")
    ap.add_argument("--tick", type=float, default=0, help="periode du scorer (0 = continu)")
    ap.add_argument("--rival-min", type=float, default=0.2, help="intervalle plancher du rival")
    ap.add_argument("--rival-interval", type=float, default=0, help="cadence FIXE du rival (0 = adaptative)")
    ap.add_argument("--rival", action="store_true", default=True)
    ARGS = ap.parse_args()

    if ARGS.rival:
        threading.Thread(target=rival_loop, daemon=True).start()
    if ARGS.reset_every > 0:
        threading.Thread(target=reset_loop, daemon=True).start()
    if ARGS.tick > 0:
        threading.Thread(target=tick_loop, args=(ARGS.tick,), daemon=True).start()

    srv = ThreadingHTTPServer(("127.0.0.1", ARGS.port), Handler)
    print("mock_rival on 127.0.0.1:%d aggression=%d reset_every=%s ratelimit=%.2f tick=%s"
          % (ARGS.port, ARGS.aggression, ARGS.reset_every or "off", ARGS.ratelimit,
             ARGS.tick or "continu"),
          flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
