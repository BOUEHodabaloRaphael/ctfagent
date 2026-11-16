#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NCTF26 FINALE — KoTH generic hill-holder (parametre, zero secret en dur).
Prepare le 2026-11-15, a BRANCHER sur la vraie colline des l'ouverture (jeu 19 nov 10:00).

Principe (format annonce : "prenez une colline et tenez-la ; chaque tick rapporte des
points tant que vous restez roi") : envoyer la requete de CLAIM en continu, en parallele
(N threads), tout en sondant le STATUS pour savoir si on est #1. Watchdog integre.

NE RIEN CODER EN DUR : tout passe par variables d'env / fichier de config JSON, car
l'URL, le chemin de claim, le token et le champ "roi" ne seront connus qu'a l'ouverture.

AUTH : charge les cookies de session depuis nctf26_storage_state.json (meme session que
le client headless), et/ou un header Authorization (KOTH_AUTH). Voir README.md.

USAGE :
  # 1) a l'ouverture, remplir la config (une des deux voies) :
  export KOTH_BASE="https://arena.ctf.tg"          # ou l'host de la colline
  export KOTH_CLAIM_PATH="/plugins/koth/api/claim" # <-- A CONFIRMER sur la vraie colline
  export KOTH_CLAIM_METHOD="POST"                   # POST|GET
  export KOTH_CLAIM_BODY='{"hill":"<id>"}'          # gabarit JSON, {token} sera substitue
  export KOTH_STATUS_PATH="/plugins/koth/api/status"
  export KOTH_KING_FIELD="king"                     # champ du JSON status = equipe/roi courant
  export KOTH_OUR_ID="<notre_equipe_ou_token>"      # pour comparer au champ king
  export KOTH_THREADS=12 ; export KOTH_PERIOD=3
  # 2) lancer (laisser tourner) :
  python3 hold_hill.py            # ou : setsid nohup python3 hold_hill.py >> koth.log 2>&1 &
  # 3) --probe : un seul claim + un status, pour calibrer les chemins avant la boucle.

CONFIG (env) :
  KOTH_BASE,KOTH_CLAIM_PATH,KOTH_CLAIM_METHOD,KOTH_CLAIM_BODY,KOTH_STATUS_PATH,
  KOTH_KING_FIELD,KOTH_OUR_ID,KOTH_TOKEN,KOTH_AUTH (header Authorization complet),
  KOTH_HEADERS (JSON extra headers),KOTH_THREADS(=10),KOTH_PERIOD(=3),
  KOTH_STORAGE (defaut: ../nctf26_storage_state.json),KOTH_TIMEOUT(=15)

REGLES (ne jamais enfreindre) : agir UNIQUEMENT sur la colline in-scope du jeu ;
pas de DoS, pas d'attaque des autres equipes / de l'infra orga.
"""
import os, sys, json, time, threading, argparse
from pathlib import Path

try:
    import requests
except ImportError:
    import subprocess
    subprocess.call([sys.executable, "-m", "pip", "install", "--quiet", "requests"])
    import requests

HERE = Path(__file__).resolve().parent

def env(name, default=None):
    return os.environ.get(name, default)

BASE        = (env("KOTH_BASE", "https://arena.ctf.tg") or "").rstrip("/")
CLAIM_PATH  = env("KOTH_CLAIM_PATH", "")
CLAIM_METH  = env("KOTH_CLAIM_METHOD", "POST").upper()
CLAIM_BODY  = env("KOTH_CLAIM_BODY", "")
STATUS_PATH = env("KOTH_STATUS_PATH", "")
KING_FIELD  = env("KOTH_KING_FIELD", "king")
OUR_ID      = env("KOTH_OUR_ID", "")
TOKEN       = env("KOTH_TOKEN", "")
AUTH        = env("KOTH_AUTH", "")
THREADS     = int(env("KOTH_THREADS", "10"))
PERIOD      = float(env("KOTH_PERIOD", "3"))
TIMEOUT     = float(env("KOTH_TIMEOUT", "15"))
STORAGE     = env("KOTH_STORAGE", str(HERE.parent / "nctf26_storage_state.json"))

_stats = {"claims": 0, "ok": 0, "err": 0}
_lock = threading.Lock()
_stop = threading.Event()

def log(*a):
    print("[%s] " % time.strftime("%H:%M:%S") + " ".join(str(x) for x in a), flush=True)

def load_cookies():
    try:
        st = json.loads(Path(STORAGE).read_text())
        return {c["name"]: c["value"] for c in st.get("cookies", [])}
    except Exception as e:
        log("WARN cookies:", e); return {}

def headers():
    h = {"Content-Type": "application/json"}
    if AUTH:
        h["Authorization"] = AUTH
    extra = env("KOTH_HEADERS")
    if extra:
        try: h.update(json.loads(extra))
        except Exception: pass
    return h

def session():
    s = requests.Session()
    s.headers.update(headers())
    ck = load_cookies()
    for k, v in ck.items():
        s.cookies.set(k, v)
    return s

def body():
    if not CLAIM_BODY:
        return None
    return CLAIM_BODY.replace("{token}", TOKEN)

def claim_once(s):
    url = BASE + CLAIM_PATH
    try:
        if CLAIM_METH == "GET":
            r = s.get(url, timeout=TIMEOUT)
        else:
            data = body()
            r = s.request(CLAIM_METH, url, data=data, timeout=TIMEOUT)
        with _lock:
            _stats["claims"] += 1
            _stats["ok" if r.status_code < 400 else "err"] += 1
        return r
    except Exception:
        with _lock:
            _stats["claims"] += 1; _stats["err"] += 1
        return None

def worker():
    s = session()
    while not _stop.is_set():
        claim_once(s)
        # pas de sleep agressif : petite pause pour ne pas DoS, ajustable
        time.sleep(0.05)

def status_line(s):
    if not STATUS_PATH:
        return "status: (KOTH_STATUS_PATH non defini)"
    try:
        j = s.get(BASE + STATUS_PATH, timeout=TIMEOUT).json()
    except Exception as e:
        return f"status: erreur ({e})"
    king = j.get(KING_FIELD) if isinstance(j, dict) else None
    mine = (OUR_ID and str(king) == str(OUR_ID))
    return f"roi={king} ROI(nous)={mine} claims={_stats['claims']} ok={_stats['ok']} err={_stats['err']}"

def probe():
    s = session()
    log("PROBE claim ->", BASE + CLAIM_PATH, "(", CLAIM_METH, ")")
    r = claim_once(s)
    log("  claim:", (r.status_code if r is not None else "EXC"),
        (r.text[:200] if r is not None else ""))
    log("PROBE status ->", BASE + STATUS_PATH)
    log("  ", status_line(s))

def main():
    ap = argparse.ArgumentParser(description="KoTH hill-holder (NCTF26 finale)")
    ap.add_argument("--probe", action="store_true", help="un claim + un status puis quitter (calibrage)")
    args = ap.parse_args()
    if not CLAIM_PATH:
        log("ERREUR: KOTH_CLAIM_PATH vide. Remplir la config (voir README.md) a l'ouverture.")
        sys.exit(2)
    if args.probe:
        probe(); return
    log(f"HOLD colline {BASE}{CLAIM_PATH} | {THREADS} threads | status/{PERIOD}s")
    ts = [threading.Thread(target=worker, daemon=True) for _ in range(THREADS)]
    for t in ts: t.start()
    mon = session()
    try:
        while True:
            time.sleep(PERIOD)
            log(status_line(mon))
    except KeyboardInterrupt:
        _stop.set(); log("arret demande (Ctrl+C)")

if __name__ == "__main__":
    main()
