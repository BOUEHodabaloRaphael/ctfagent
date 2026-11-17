#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NCTF26 FINALE — teneur de colline KoTH (HTTP claim). Stdlib only, offline-safe.

But : garder une colline "claim HTTP" du debut a la fin, de facon persistante et
respectueuse (pas de DoS). Tout est parametre par variables d'env : rien n'est code
en dur, car l'URL / le chemin / le format de claim ne sont connus qu'a l'ouverture.

Patterns repris du kit prequal (Th3N00bs + deploy/) et corriges :
  - creneaux alignes (slots) facon throne_hold_timed_safe.py : viser le tick du scorer
    au lieu de matraquer en continu ;
  - redirections interdites : le payload de claim ne part JAMAIS vers une autre URL ;
  - une mutation incertaine n'est jamais rejouee automatiquement (pas de double claim) ;
  - cadence plafonnee + jitter + backoff sur 429/503 (respect Retry-After) ;
  - etat sur disque (status.json / pid.json) + arret propre via fichier STOP ;
  - support optionnel des claims signes (HMAC), du bearer, des cookies de session.

MODES
  --probe    1 claim + 1 status, puis sortie (calibrage a t+0)
  --run      boucle de tenue (ce que lance koth_hold.sh)
  --once    1 claim seulement (test manuel)

CONFIG (env, voir hill.env.example)
  KOTH_BASE, KOTH_CLAIM_PATH, KOTH_CLAIM_METHOD, KOTH_CLAIM_BODY, KOTH_STATUS_PATH,
  KOTH_KING_FIELD, KOTH_OUR_ID, KOTH_TOKEN, KOTH_AUTH, KOTH_HEADERS, KOTH_THREADS,
  KOTH_MIN_INTERVAL, KOTH_SLOT_PERIOD, KOTH_PERIOD, KOTH_TIMEOUT, KOTH_STORAGE,
  KOTH_STOP_FILE, KOTH_UNTIL, KOTH_SIGN_KEY, KOTH_SIGN_ALGO, KOTH_PROXY, KOTH_STATE_DIR

REGLES : colline in-scope uniquement. Pas de DoS, pas d'attaque des autres equipes
ni de l'infra organisatrice.
"""
import argparse
import hashlib
import hmac
import json
import os
import random
import signal
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent


# --------------------------------------------------------------------------- env
def env(name, default=None):
    v = os.environ.get(name)
    return default if v is None or v == "" else v


BASE = (env("KOTH_BASE", "https://arena.ctf.tg") or "").rstrip("/")
CLAIM_PATH = env("KOTH_CLAIM_PATH", "")
CLAIM_METH = env("KOTH_CLAIM_METHOD", "POST").upper()
CLAIM_BODY = env("KOTH_CLAIM_BODY", "")
STATUS_PATH = env("KOTH_STATUS_PATH", "")
KING_FIELD = env("KOTH_KING_FIELD", "king")
OUR_IDS = [x.strip() for x in (env("KOTH_OUR_ID", "") or "").split(",") if x.strip()]
TOKEN = env("KOTH_TOKEN", "")
AUTH = env("KOTH_AUTH", "")
THREADS = max(1, int(env("KOTH_THREADS", "4")))
MIN_INTERVAL = float(env("KOTH_MIN_INTERVAL", "1.0"))   # par thread, plancher anti-DoS
SLOT_PERIOD = float(env("KOTH_SLOT_PERIOD", "0"))       # 0 = pas de slots
SLOT_MARGIN = float(env("KOTH_SLOT_MARGIN", "0.4"))     # arriver un peu avant le tick
PERIOD = float(env("KOTH_PERIOD", "5"))                 # cadence du status
TIMEOUT = float(env("KOTH_TIMEOUT", "15"))
STORAGE = env("KOTH_STORAGE", str(HERE.parent / "nctf26_storage_state.json"))
STOP_FILE = Path(env("KOTH_STOP_FILE", str(HERE / "STOP")))
UNTIL = env("KOTH_UNTIL", "")                           # ex: 2026-11-19T23:00:00Z
SIGN_KEY = env("KOTH_SIGN_KEY", "")
SIGN_ALGO = env("KOTH_SIGN_ALGO", "hmac-sha1").lower()
PROXY = env("KOTH_PROXY", "")
STATE_DIR = Path(env("KOTH_STATE_DIR", str(HERE)))
STATUS_JSON = STATE_DIR / "status.json"
PID_JSON = STATE_DIR / "pid.json"

_stop = threading.Event()
_lock = threading.Lock()
_stats = {"claims": 0, "ok": 0, "err": 0, "last_code": None, "king": None, "is_king": None,
          "started": time.time(), "last_claim": 0.0, "slot_period": SLOT_PERIOD}


def log(*a):
    print("[%s] %s" % (time.strftime("%H:%M:%S"), " ".join(str(x) for x in a)), flush=True)


def stop_requested():
    return _stop.is_set() or STOP_FILE.exists() or _until_reached()


def _until_reached():
    if not UNTIL:
        return False
    try:
        return time.time() >= _parse_utc(UNTIL)
    except Exception:
        return False


def _parse_utc(s):
    s = s.strip().replace("Z", "+00:00")
    import datetime
    return datetime.datetime.fromisoformat(s).timestamp()


# ------------------------------------------------------------------------ client
class NoRedirect(urllib.request.HTTPRedirectHandler):
    """Ne jamais transmettre le payload de claim a une autre URL."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _opener():
    handlers = [NoRedirect()]
    if PROXY:
        handlers.append(urllib.request.ProxyHandler({"http": PROXY, "https": PROXY}))
    else:
        handlers.append(urllib.request.ProxyHandler({}))  # ignore les proxies hérités
    return urllib.request.build_opener(*handlers)


def load_cookies():
    p = Path(STORAGE)
    if not p.exists():
        return {}  # pas de session : la colline s'authentifie peut-etre par token
    try:
        st = json.loads(p.read_text())
        return {c["name"]: c["value"] for c in st.get("cookies", []) if c.get("name")}
    except Exception as e:
        log("WARN cookies:", e)
        return {}


def base_headers():
    h = {"Content-Type": "application/json", "User-Agent": "nctf26-koth-hold/1.0"}
    if AUTH:
        h["Authorization"] = AUTH
    extra = env("KOTH_HEADERS")
    if extra:
        try:
            h.update(json.loads(extra))
        except Exception as e:
            log("WARN KOTH_HEADERS:", e)
    return h


def _sign(team, ts):
    if not SIGN_KEY:
        return ""
    algo = {"hmac-sha1": hashlib.sha1, "hmac-sha256": hashlib.sha256}.get(SIGN_ALGO)
    if algo is None:
        raise SystemExit("KOTH_SIGN_ALGO inconnu: %s" % SIGN_ALGO)
    msg = ("%s|%d" % (team, ts)).encode()
    return hmac.new(SIGN_KEY.encode(), msg, algo).hexdigest()


def claim_body():
    if not CLAIM_BODY:
        return None
    ts = int(time.time())
    body = CLAIM_BODY
    body = body.replace("{token}", TOKEN).replace("{team}", TOKEN).replace("{ts}", str(ts))
    if "{sig}" in body:
        body = body.replace("{sig}", _sign(TOKEN, ts))
    return body.encode()


def claim_once(opener, cookies):
    url = BASE + CLAIM_PATH
    data = None if CLAIM_METH == "GET" else claim_body()
    req = urllib.request.Request(url, data=data, headers=base_headers(), method=CLAIM_METH)
    if cookies:
        req.add_header("Cookie", "; ".join("%s=%s" % (k, v) for k, v in cookies.items()))
    code, text, retry_after = None, "", None
    try:
        with opener.open(req, timeout=TIMEOUT) as r:
            code = r.status
            text = r.read(512).decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        code = e.code
        retry_after = e.headers.get("Retry-After")
        try:
            text = e.read(256).decode("utf-8", "replace")
        except Exception:
            text = ""
    except Exception as e:
        with _lock:
            _stats["claims"] += 1
            _stats["err"] += 1
            _stats["last_code"] = "EXC:%s" % type(e).__name__
        return None, 0.0
    with _lock:
        _stats["claims"] += 1
        _stats["ok" if code and code < 400 else "err"] += 1
        _stats["last_code"] = code
        _stats["last_claim"] = time.time()
    return code, (float(retry_after) if retry_after and retry_after.isdigit() else 0.0)


def status_snapshot(opener, cookies):
    if not STATUS_PATH:
        return None
    req = urllib.request.Request(BASE + STATUS_PATH, headers=base_headers(), method="GET")
    if cookies:
        req.add_header("Cookie", "; ".join("%s=%s" % (k, v) for k, v in cookies.items()))
    try:
        with opener.open(req, timeout=TIMEOUT) as r:
            raw = r.read(20000).decode("utf-8", "replace")
    except Exception as e:
        return {"error": "%s" % type(e).__name__}
    try:
        j = json.loads(raw)
    except Exception:
        return {"error": "not-json", "raw": raw[:160]}
    king = j
    for part in KING_FIELD.split("."):
        if isinstance(king, dict) and part in king:
            king = king[part]
        else:
            king = None
            break
    with _lock:
        _stats["king"] = king
        _stats["is_king"] = bool(king is not None and str(king) in OUR_IDS)
    return j


def write_status(opener=None, cookies=None):
    with _lock:
        snap = dict(_stats)
    snap["king_field"] = KING_FIELD
    snap["our_ids"] = OUR_IDS
    snap["threads"] = THREADS
    snap["min_interval"] = MIN_INTERVAL
    snap["uptime_s"] = round(time.time() - snap["started"], 1)
    snap["pid"] = os.getpid()
    snap["stop"] = stop_requested()
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        tmp = STATUS_JSON.with_suffix(".tmp")
        tmp.write_text(json.dumps(snap, indent=2, default=str))
        tmp.replace(STATUS_JSON)
    except Exception as e:
        log("WARN status.json:", e)
    return snap


# ----------------------------------------------------------------------- workers
def next_slot_start(anchor, period, margin):
    now = time.time()
    k = max(0, int((now + margin - anchor) // period) + 1)
    tick = anchor + k * period
    return tick - margin


def worker(idx, opener, cookies, anchor):
    rnd = random.Random(idx * 7919)
    while not stop_requested():
        if SLOT_PERIOD > 0:
            target = next_slot_start(anchor, SLOT_PERIOD, SLOT_MARGIN)
            while time.time() < target and not stop_requested():
                time.sleep(min(0.2, max(0.0, target - time.time())))
            if stop_requested():
                return
        code, retry_after = claim_once(opener, cookies)
        if code in (429, 503):
            back = retry_after or 5.0
            log("thread%d HTTP %s -> backoff %.1fs" % (idx, code, back))
            time.sleep(back)
            continue
        if code is None or (isinstance(code, int) and code >= 500):
            time.sleep(min(10.0, 2.0 * (1 + rnd.random())))
            continue
        if SLOT_PERIOD <= 0:
            time.sleep(MIN_INTERVAL * (0.8 + 0.4 * rnd.random()))


# -------------------------------------------------------------------------- main
def preflight():
    if not CLAIM_PATH:
        log("ERREUR: KOTH_CLAIM_PATH vide -> remplir hill.env (voir README.md)")
        return False
    if not OUR_IDS:
        log("WARN: KOTH_OUR_ID vide -> on ne saura pas confirmer ROI=OUI")
    if SLOT_PERIOD and SLOT_PERIOD < 1:
        log("WARN: KOTH_SLOT_PERIOD < 1s, ignoré")
    return True


def probe():
    opener, cookies = _opener(), load_cookies()
    log("PROBE claim ->", BASE + CLAIM_PATH, "(%s)" % CLAIM_METH)
    code, _ = claim_once(opener, cookies)
    log("  claim:", code)
    if STATUS_PATH:
        log("PROBE status ->", BASE + STATUS_PATH)
        j = status_snapshot(opener, cookies)
        log("  roi=%s ROI(nous)=%s" % (_stats["king"], _stats["is_king"]))
        if j is not None and "error" not in (j or {}):
            log("  status keys:", list(j)[:8] if isinstance(j, dict) else type(j).__name__)
    write_status()
    return 0


def run():
    if not preflight():
        return 2
    if STOP_FILE.exists():
        log("STOP present -> rien a faire (rm %s pour relancer)" % STOP_FILE)
        return 0
    opener, cookies = _opener(), load_cookies()
    anchor = time.time()
    if SLOT_PERIOD > 0:
        anchor = anchor - (anchor % SLOT_PERIOD)  # slots alignes sur l'horloge
    log("HOLD %s%s | threads=%d | min_interval=%.2fs | slot=%s | until=%s"
        % (BASE, CLAIM_PATH, THREADS, MIN_INTERVAL, SLOT_PERIOD or "off", UNTIL or "fin"))
    if cookies:
        log("auth: cookies session (%d) + %s" % (len(cookies), "bearer" if AUTH else "sans bearer"))
    ts = [threading.Thread(target=worker, args=(i, opener, cookies, anchor), daemon=True)
          for i in range(THREADS)]
    for t in ts:
        t.start()
    while not stop_requested():
        time.sleep(min(PERIOD, 1.0) if PERIOD < 1 else 1.0)
        with _lock:
            last = _stats["last_claim"]
        if PERIOD and time.time() - getattr(run, "_last_snap", 0) >= PERIOD:
            if STATUS_PATH:
                status_snapshot(opener, cookies)
            snap = write_status()
            run._last_snap = time.time()
            log("claims=%d ok=%d err=%d last=%s roi=%s ROI(nous)=%s"
                % (snap["claims"], snap["ok"], snap["err"], snap["last_code"],
                   snap["king"], snap["is_king"]))
    _stop.set()
    for t in ts:
        t.join(timeout=3)
    write_status()
    log("arret propre (claims=%d)" % _stats["claims"])
    return 0


def main():
    ap = argparse.ArgumentParser(description="KoTH hill-holder HTTP (NCTF26 finale)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--run", action="store_true", help="boucle de tenue")
    g.add_argument("--probe", action="store_true", help="1 claim + 1 status puis sortie")
    g.add_argument("--once", action="store_true", help="1 claim seulement")
    args = ap.parse_args()

    def _sig(_s, _f):
        _stop.set()

    signal.signal(signal.SIGTERM, _sig)
    signal.signal(signal.SIGINT, _sig)
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    if args.probe:
        return probe()
    if args.once:
        if not preflight():
            return 2
        code, _ = claim_once(_opener(), load_cookies())
        log("claim:", code)
        return 0 if code and code < 400 else 1
    return run()


if __name__ == "__main__":
    sys.exit(main())
