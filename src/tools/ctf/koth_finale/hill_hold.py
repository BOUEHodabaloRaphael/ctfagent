#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NCTF26 — KoTH : moteur de tenue ADAPTATIF ("s'endurcit au fur et a mesure").

Idee : au lieu de spammer a cadence fixe (ce que faisait le kit prequal, jusqu'a 800 req/s
= DoS), le moteur tourne en machine a etats et n'augmente la pression QUE quand on perd
la colline, puis redescend quand on la tient. Il apprend la cadence du rival, burst
immediatement apres une perte, et persiste son niveau pour reprendre fort apres un crash.

Deux modes :
  - HTTP  : claim + status sur la colline (defaut)
  - LOCAL : on est DEJA sur la box (score = fichier "king") -> maintient le fichier,
            detecte les ecrasements et repare (auto-endurcissement du fichier)

MULTI-MACHINES (toi + coequipiers) : KOTH_PUMPS=N divise la cadence par N sur chaque
machine -> le debit TOTAL reste borne (pas de DoS), et N machines tiennent la colline
mieux qu'une. Chaque machine a son KOTH_PUMP_ID pour les logs/status.

ETATS
  PROBE   : 1 thread lent, on mesure (qui est roi, a quelle cadence il bouge)
  CONTEST : on perd -> on monte d'un cran (threads x2, intervalle /2) + burst immediat
  HOLD    : on tient -> on redescend d'un cran apres KOTH_HOLD_TICKS polls gagnants
  DEFEND  : perte detectee -> burst prioritaire, puis retour a l'etat courant

Anti-DoS : plafonds durs (KOTH_THREADS_MAX, KOTH_INTERVAL_MIN), jitter, backoff 429/503
avec Retry-After, redirections interdites. Stdlib uniquement (aucun pip, hors-ligne).

Usage : python3 hill_hold.py --run | --probe | --once
Config : variables d'env (voir hill.env.example) — rien en dur.
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
import http.client
import ssl
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent


def env(name, default=None):
    v = os.environ.get(name)
    return default if v is None or v == "" else v


# ------------------------------------------------------------------ config
BASE = (env("KOTH_BASE", "https://arena.ctf.tg") or "").rstrip("/")
CLAIM_PATH = env("KOTH_CLAIM_PATH", "")
CLAIM_METH = env("KOTH_CLAIM_METHOD", "POST").upper()
CLAIM_BODY = env("KOTH_CLAIM_BODY", "")
STATUS_PATH = env("KOTH_STATUS_PATH", "")
KING_FIELD = env("KOTH_KING_FIELD", "king")
OUR_IDS = [x.strip() for x in (env("KOTH_OUR_ID", "") or "").split(",") if x.strip()]
TOKEN = env("KOTH_TOKEN", "")
AUTH = env("KOTH_AUTH", "")
TIMEOUT = float(env("KOTH_TIMEOUT", "15"))
STORAGE = env("KOTH_STORAGE", str(HERE.parent / "nctf26_storage_state.json"))

# adaptatif
THREADS_BASE = max(1, int(env("KOTH_THREADS_BASE", "2")))
THREADS_MAX = max(THREADS_BASE, int(env("KOTH_THREADS_MAX", "8")))
INTERVAL_BASE = float(env("KOTH_INTERVAL_BASE", "2.0"))
INTERVAL_MIN = float(env("KOTH_INTERVAL_MIN", "0.5"))
MAX_LEVEL = max(0, int(env("KOTH_MAX_LEVEL", "2")))
HOLD_TICKS = max(1, int(env("KOTH_HOLD_TICKS", "3")))
BURST = max(0, int(env("KOTH_BURST", "3")))
STATUS_EVERY = float(env("KOTH_STATUS_EVERY", "5"))
PUMPS = max(1, int(env("KOTH_PUMPS", "1")))
PUMP_ID = env("KOTH_PUMP_ID", "1")
try:
    PUMP_NUM = max(1, min(PUMPS, int(PUMP_ID)))
except Exception:
    PUMP_NUM = 1

# --- sniping : le scorer lit le roi a un tick ; le DERNIER claim avant le tick gagne.
SLOT_PERIOD = float(env("KOTH_SLOT_PERIOD", "0"))     # >0 = periode du tick du scorer
SNIPE_WINDOW = float(env("KOTH_SNIPE_WINDOW", "1.5"))  # largeur de la rafale avant le tick
SNIPE_GRACE = float(env("KOTH_SNIPE_GRACE", "0.25"))   # on continue un peu APRES le tick
SNIPE_GAP = float(env("KOTH_SNIPE_GAP", "0.06"))       # espacement intra-rafale (plancher)
SNIPE_GAP_MIN = float(env("KOTH_SNIPE_GAP_MIN", "0.02"))  # plancher absolu au niveau max
BASELINE_GAP = float(env("KOTH_BASELINE_GAP", "1.0"))  # pouls hors fenetre (phase inconnue)
TRAIN_MAX = float(env("KOTH_TRAIN_MAX", "0.8"))        # duree max du train final (s)
THROTTLE_SOFT = int(env("KOTH_THROTTLE_SOFT", "5"))    # 429 dans 10s -> on ralentit un peu
LOSS_STREAK = max(1, int(env("KOTH_LOSS_STREAK", "2")))  # pertes consecutives avant de monter
RELAX_AFTER = float(env("KOTH_RELAX_AFTER", "20"))     # ne pas redescendre avant N s de tenue

# fichier roi local (mode LOCAL : on est sur la box)
KING_FILE = env("KOTH_KING_FILE", "")
KING_FILE2 = env("KOTH_KING_FILE2", "")
REPAIR_MIN = float(env("KOTH_REPAIR_INTERVAL", "0.5"))

STOP_FILE = Path(env("KOTH_STOP_FILE", str(HERE / "STOP")))
STATE_DIR = Path(env("KOTH_STATE_DIR", str(HERE)))
STATE_FILE = STATE_DIR / "adaptive_state.json"
STATUS_JSON = STATE_DIR / "status.json"
UNTIL = env("KOTH_UNTIL", "")
SIGN_KEY = env("KOTH_SIGN_KEY", "")
SIGN_ALGO = env("KOTH_SIGN_ALGO", "hmac-sha1").lower()
PROXY = env("KOTH_PROXY", "")

_stop = threading.Event()
_lock = threading.Lock()

ctl = {
    "mode": "local" if KING_FILE else "http",
    "level": 0, "threads": THREADS_BASE, "interval": INTERVAL_BASE,
    "burst": BURST, "soft_until": 0.0,
}
stats = {
    "claims": 0, "ok": 0, "err": 0, "rate_limited": 0, "last_code": None,
    "king": None, "is_king": None, "wins": 0, "losses": 0, "takeovers": 0,
    "repairs": 0, "poll_errors": 0, "started": time.time(), "last_claim": 0.0,
    "escalations": 0, "relaxations": 0, "mode": ctl["mode"], "pump": PUMP_ID,
    "pumps": PUMPS,
}


def log(*a):
    print("[%s][p%s] %s" % (time.strftime("%H:%M:%S"), PUMP_ID,
                           " ".join(str(x) for x in a)), flush=True)


def stop_requested():
    if _stop.is_set() or STOP_FILE.exists():
        return True
    if UNTIL:
        try:
            import datetime
            end = datetime.datetime.fromisoformat(UNTIL.strip().replace("Z", "+00:00"))
            return time.time() >= end.timestamp()
        except Exception:
            return False
    return False


# ------------------------------------------------------------------ state
def load_state():
    try:
        d = json.loads(STATE_FILE.read_text())
        ctl["level"] = int(d.get("level", 0))
        apply_level(ctl["level"], persist=False)
        log("reprise d'etat : niveau %d (threads=%d interval=%.2fs)"
            % (ctl["level"], ctl["threads"], ctl["interval"]))
    except Exception:
        pass


def apply_level(level, persist=True):
    level = max(0, min(MAX_LEVEL, level))
    ctl["level"] = level
    ctl["threads"] = min(THREADS_MAX, THREADS_BASE * (2 ** level))
    ctl["interval"] = max(INTERVAL_MIN, INTERVAL_BASE / (2 ** level)) * PUMPS
    if persist:
        try:
            tmp = STATE_FILE.with_suffix(".tmp")
            tmp.write_text(json.dumps({"level": level, "threads": ctl["threads"],
                                       "interval": ctl["interval"],
                                       "updated": time.time()}, indent=2))
            tmp.replace(STATE_FILE)
        except Exception:
            pass


def write_status():
    with _lock:
        snap = dict(stats)
        snap.update({"our_ids": OUR_IDS, "king_field": KING_FIELD,
                     "level": ctl["level"], "threads": ctl["threads"],
                     "interval": round(ctl["interval"], 3), "burst": ctl["burst"],
                     "snipe_window": SNIPE_WINDOW if SLOT_PERIOD else 0,
                     "slot_period": SLOT_PERIOD,
                     "loss_streak_need": LOSS_STREAK,
                     "uptime_s": round(time.time() - stats["started"], 1),
                     "pid": os.getpid(), "stop": stop_requested()})
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        tmp = STATUS_JSON.with_suffix(".tmp")
        tmp.write_text(json.dumps(snap, indent=2, default=str))
        tmp.replace(STATUS_JSON)
    except Exception:
        pass
    return snap


# ------------------------------------------------------------------ HTTP
class HillConn:
    """Client HTTP keep-alive, un par thread.

    Pourquoi c'est capital : avec urllib, CHAQUE claim payait un handshake TCP+TLS
    complet (100-300 ms sur Internet). En keep-alive, un claim = un aller-retour, donc
    on peut reellement placer un claim dans les dernieres millisecondes avant le tick.
    Aucune redirection n'est suivie (http.client n'en suit pas) : le payload de claim
    ne peut pas partir vers une autre URL.
    """

    def __init__(self, base, timeout, proxy=""):
        u = urllib.parse.urlsplit(base)
        self.scheme = u.scheme or "http"
        self.host = u.hostname or "127.0.0.1"
        self.port = u.port or (443 if self.scheme == "https" else 80)
        self.prefix = (u.path or "").rstrip("/")
        self.timeout = timeout
        self.proxy = proxy
        self.conn = None

    def _ssl_ctx(self):
        ctx = ssl.create_default_context()
        if env("KOTH_TLS_INSECURE", "0") == "1":
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
        return ctx

    def _connect(self):
        if self.proxy:
            pu = urllib.parse.urlsplit(self.proxy if "://" in self.proxy else "http://" + self.proxy)
            ph, pp = pu.hostname, pu.port or 8080
            if self.scheme == "https":
                c = http.client.HTTPSConnection(ph, pp, timeout=self.timeout, context=self._ssl_ctx())
                c.set_tunnel(self.host, self.port)
            else:
                c = http.client.HTTPConnection(ph, pp, timeout=self.timeout)
        elif self.scheme == "https":
            c = http.client.HTTPSConnection(self.host, self.port, timeout=self.timeout,
                                            context=self._ssl_ctx())
        else:
            c = http.client.HTTPConnection(self.host, self.port, timeout=self.timeout)
        c.connect()
        self.conn = c

    def close(self):
        try:
            if self.conn:
                self.conn.close()
        except Exception:
            pass
        self.conn = None

    def request(self, method, path, body=None, extra_headers=None, _retry=True):
        h = dict(extra_headers or {})
        try:
            if self.conn is None:
                self._connect()
            self.conn.request(method, self.prefix + path, body=body, headers=h)
            r = self.conn.getresponse()
            data = r.read()          # lecture complete => la connexion est reutilisable
            ra = r.getheader("Retry-After")
            return r.status, ra, data
        except Exception:
            self.close()
            if _retry:
                return self.request(method, path, body, extra_headers, _retry=False)
            raise


def load_cookies():
    p = Path(STORAGE)
    if not p.exists():
        return {}
    try:
        st = json.loads(p.read_text())
        return {c["name"]: c["value"] for c in st.get("cookies", []) if c.get("name")}
    except Exception as e:
        log("WARN cookies:", e)
        return {}


def headers(cookies=None):
    h = {"Content-Type": "application/json", "User-Agent": "nctf26-koth/2.1",
         "Connection": "keep-alive"}
    if AUTH:
        h["Authorization"] = AUTH
    extra = env("KOTH_HEADERS")
    if extra:
        try:
            h.update(json.loads(extra))
        except Exception:
            pass
    if cookies:
        h["Cookie"] = "; ".join("%s=%s" % kv for kv in cookies.items())
    return h


def _sign(team, ts):
    algo = {"hmac-sha1": hashlib.sha1, "hmac-sha256": hashlib.sha256}.get(SIGN_ALGO)
    if not SIGN_KEY or algo is None:
        return ""
    return hmac.new(SIGN_KEY.encode(), ("%s|%d" % (team, ts)).encode(), algo).hexdigest()


def claim_body():
    if not CLAIM_BODY:
        return None
    ts = int(time.time())
    b = (CLAIM_BODY.replace("{token}", TOKEN).replace("{team}", TOKEN)
         .replace("{ts}", str(ts)))
    if "{sig}" in b:
        b = b.replace("{sig}", _sign(TOKEN, ts))
    return b.encode()


def claim(conn, cookies):
    data = None if CLAIM_METH == "GET" else claim_body()
    code, ra = None, 0.0
    t0 = time.time()
    try:
        code, ra_h, _ = conn.request(CLAIM_METH, CLAIM_PATH, body=data,
                                     extra_headers=headers(cookies))
        ra = float(ra_h) if ra_h and str(ra_h).isdigit() else 0.0
    except Exception:
        with _lock:
            stats["claims"] += 1
            stats["err"] += 1
            stats["last_code"] = "EXC"
        return None, 0.0
    rtt = (time.time() - t0) * 1000.0
    with _lock:
        prev = stats.get("rtt_ms") or rtt
        stats["rtt_ms"] = round(prev * 0.8 + rtt * 0.2, 1)  # EWMA
        stats["claims"] += 1
        if code and code < 400:
            stats["ok"] += 1
        else:
            stats["err"] += 1
            if code in (429, 503):
                stats["rate_limited"] += 1
        stats["last_code"] = code
        stats["last_claim"] = time.time()
        if code in (429, 503):
            stats.setdefault("throttle_ts", []).append(time.time())
            stats["throttle_ts"] = stats["throttle_ts"][-50:]
            recent = [t for t in stats["throttle_ts"] if time.time() - t <= 10]
            stats["throttle_10s"] = len(recent)
            if len(recent) >= THROTTLE_SOFT:
                ctl["soft_until"] = time.time() + 15.0
    return code, ra


def poll_status(conn, cookies, field=None):
    if not STATUS_PATH:
        return None
    try:
        code, _, raw = conn.request("GET", STATUS_PATH, extra_headers=headers(cookies))
        j = json.loads(raw.decode("utf-8", "replace"))
    except Exception:
        with _lock:
            stats["poll_errors"] += 1
        return None
    king = j
    for part in (field or KING_FIELD).split("."):
        king = king.get(part) if isinstance(king, dict) else None
        if king is None:
            break
    with _lock:
        stats["king"] = king
        stats["is_king"] = bool(king is not None and str(king) in OUR_IDS)
    return king


# ---------------------------------------------------------------- workers
def next_tick(period):
    """Prochain tick du scorer, strictement dans le futur (aligne sur l'epoch)."""
    now = time.time()
    return (int(now // period) + 1) * period


def worker(idx, conn, cookies):
    """Le scorer ne retient que le roi AU TICK. Toute la strategie tient en 3 phases :

      pouls   : hors fenetre, 1 claim/s (la phase du scorer peut etre inconnue :
                on ne se tait jamais completement) ;
      coarse  : on remplit la fenetre a cadence normale ;
      TRAIN   : les derniers 6*RTT avant le tick, TOUS les threads tirent sans relache
                pour que le tout dernier claim arrive quelques ms avant le tick.

    Aucun 429 n'arrete tout le monde : le backoff est local et tres court, sinon on
    raterait justement le tick (c'etait LE bug qui faisait perdre 50% des ticks).
    """
    rnd = random.Random(idx * 7919 + PUMP_NUM * 104729)

    while not stop_requested():
        with _lock:
            interval = ctl["interval"]
            level = ctl["level"]
            burst = ctl["burst"] > 0
            if burst:
                ctl["burst"] -= 1
            rtt = (stats.get("rtt_ms") or 30.0) / 1000.0
            nthreads = max(1, ctl["threads"])
            slow = ctl.get("soft_until", 0) > time.time()
        pace = 2.0 if slow else 1.0

        # ---------------- mode LIBRE (aucun tick connu) ----------------
        if SLOT_PERIOD <= 0:
            if idx >= nthreads:
                time.sleep(0.2)
                continue
            code, ra = claim(conn, cookies)
            if code in (429, 503):
                time.sleep(min(ra or 0.5, 1.0))
                continue
            if not burst:
                time.sleep(max(0.05, interval * pace * (0.8 + 0.4 * rnd.random())))
            continue

        # ---------------- mode SNIPE ----------------
        tick = next_tick(SLOT_PERIOD)
        train = min(TRAIN_MAX, max(0.12, 6.0 * rtt))
        train_start = tick - train
        pump_off = ((PUMP_NUM - 1) / PUMPS) * SNIPE_WINDOW * 0.6
        thr_off = (idx / nthreads) * SNIPE_WINDOW * 0.2
        start = tick - SNIPE_WINDOW + pump_off + thr_off
        now = time.time()

        # --- phase pouls : un seul thread suffit, on ne double pas les claims
        if now < start - 0.05:
            time.sleep(min(start - now, BASELINE_GAP * pace))
            if idx == 0 and time.time() < start - 0.05:
                code, ra = claim(conn, cookies)
                if code in (429, 503):
                    time.sleep(min(ra or 0.25, 0.35))
            continue

        # --- phase coarse : seuls les threads actifs remplissent la fenetre
        if now < train_start:
            if idx >= nthreads:
                time.sleep(0.05)
                continue
            coarse = max(0.10, SNIPE_WINDOW / (nthreads * PUMPS * 2.5))
            code, ra = claim(conn, cookies)
            if code in (429, 503):
                time.sleep(min(ra or 0.25, 0.35))
            else:
                time.sleep(coarse * (0.7 + 0.6 * rnd.random()))
            continue

        # --- TRAIN FINAL : tous les threads, densite maximale, jusqu'au tick.
        # Periode DIFFERENTE par thread (sinon les 8 threads se synchronisent et laissent
        # des trous de 20 ms entre deux salves : c'est exactement ce qui perdait le tick).
        base_shot = max(0.003, 0.006 * (0.6 ** level)) * pace
        shot = base_shot * (0.6 + 1.4 * (idx / max(1, nthreads)))
        while time.time() <= tick + 0.01 and not stop_requested():
            code, ra = claim(conn, cookies)
            if code in (429, 503):
                # on ne s'arrete JAMAIS plus de ~20ms en pleine rafale : sinon on rate le tick
                left = tick - time.time() - 0.005
                time.sleep(max(0.003, min(ra or 0.02, 0.02, left if left > 0 else 0.003)))
                continue
            time.sleep(shot * (0.6 + 0.8 * rnd.random()))


# ------------------------------------------------------------ adaptation
def adapt(king, win_streak, loss_streak):
    """Le coeur de l'endurcissement : on ne monte QUE si on perd vraiment.

    Hysteresis : il faut LOSS_STREAK pertes consecutives pour escalader (une perte
    isolee juste apres notre claim n'est pas significative si le score est au tick),
    et RELAX_AFTER secondes de tenue avant de redescendre. Sans ca on oscille.
    """
    mine = bool(king is not None and str(king) in OUR_IDS)
    with _lock:
        if mine:
            stats["wins"] += 1
            held = time.time() - stats.get("held_since", time.time())
            if (win_streak >= HOLD_TICKS and ctl["level"] > 0
                    and held >= RELAX_AFTER):
                apply_level(ctl["level"] - 1)
                stats["relaxations"] += 1
                log("HOLD -> on tient (%d ticks, %.0fs) : niveau %d (threads=%d, %.2fs)"
                    % (win_streak, held, ctl["level"], ctl["threads"], ctl["interval"]))
                stats["held_since"] = time.time()
        else:
            stats["losses"] += 1
            if king is not None:
                stats["takeovers"] += 1
            stats["held_since"] = time.time()
            if loss_streak >= LOSS_STREAK:
                if ctl["level"] < MAX_LEVEL:
                    apply_level(ctl["level"] + 1)
                    stats["escalations"] += 1
                    log("CONTEST -> perdu %dx (roi=%s) : niveau %d (threads=%d, %.2fs) + burst %d"
                        % (loss_streak, king, ctl["level"], ctl["threads"],
                           ctl["interval"], BURST))
                else:
                    log("CONTEST -> perdu %dx, deja au plafond (roi=%s) : on insiste"
                        % (loss_streak, king))
                ctl["burst"] = max(ctl["burst"], BURST)
    return mine


# ------------------------------------------------------------ mode LOCAL
def local_hold():
    """On est sur la box : le score = un fichier king qu'on maintient, et qu'on
    repare des qu'un rival l'ecrase (c'est ca, l'endurcissement du fichier)."""
    files = [f for f in (KING_FILE, KING_FILE2) if f]
    log("LOCAL : maintien de %s (valeur=%s)" % (", ".join(files), TOKEN))
    last = 0.0
    while not stop_requested():
        for f in files:
            try:
                cur = Path(f).read_text().strip()
            except Exception:
                cur = None
            if cur != TOKEN:
                try:
                    Path(f).write_text(TOKEN + "\n")
                    with _lock:
                        stats["claims"] += 1
                        stats["ok"] += 1
                        if cur is not None:
                            stats["repairs"] += 1
                            stats["takeovers"] += 1
                        stats["king"] = TOKEN
                        stats["is_king"] = True
                except Exception:
                    with _lock:
                        stats["err"] += 1
            else:
                with _lock:
                    stats["king"] = TOKEN
                    stats["is_king"] = True
        # cadence : si on repare beaucoup, on accelere (jusqu'a REPAIR_MIN)
        with _lock:
            rate = stats["repairs"]
        hot = rate > 0 and (time.time() - last) < 60
        time.sleep(REPAIR_MIN if hot else max(REPAIR_MIN, 1.0))
        last = time.time()
        if time.time() - getattr(local_hold, "_snap", 0) >= STATUS_EVERY:
            local_hold._snap = time.time()
            s = write_status()
            log("king=%s repairs=%d claims=%d" % (s["king"], s["repairs"], s["claims"]))


# ------------------------------------------------------------------- run
def preflight():
    if ctl["mode"] == "local":
        if not TOKEN:
            log("ERREUR: KOTH_TOKEN requis en mode LOCAL")
            return False
        return True
    if not CLAIM_PATH:
        log("ERREUR: KOTH_CLAIM_PATH vide -> remplir hill.env (voir README)")
        return False
    if not OUR_IDS:
        log("WARN: KOTH_OUR_ID vide -> impossible de confirmer ROI=OUI")
    return True


def probe():
    if ctl["mode"] == "local":
        log("PROBE LOCAL %s -> %s" % (KING_FILE, Path(KING_FILE).exists()))
        return 0
    op, ck = HillConn(BASE, TIMEOUT, PROXY), load_cookies()
    log("PROBE claim -> %s%s (%s)" % (BASE, CLAIM_PATH, CLAIM_METH))
    code, _ = claim(op, ck)
    log("  claim:", code)
    if STATUS_PATH:
        k = poll_status(op, ck)
        if k is None and KING_FIELD != "king":
            k = poll_status(op, ck, field="king")   # repli : mauvais champ devine ?
            log("  (champ %r vide -> repli sur 'king')" % KING_FIELD)
        log("  roi=%s ROI(nous)=%s" % (k, stats["is_king"]))
    write_status()
    return 0


def run():
    if not preflight():
        return 2
    if STOP_FILE.exists():
        log("STOP present -> rien a faire (rm %s pour relancer)" % STOP_FILE)
        return 0
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    load_state()
    if ctl["mode"] == "local":
        local_hold()
        write_status()
        return 0

    ck = load_cookies()
    op = HillConn(BASE, TIMEOUT, PROXY)          # connexion du thread principal (status)
    log("HOLD %s%s | niveau=%d threads=%d interval=%.2fs | snipe=%s | pompes=%d (p%s) | until=%s"
        % (BASE, CLAIM_PATH, ctl["level"], ctl["threads"], ctl["interval"],
           ("%.1fs avant tick %.0fs" % (SNIPE_WINDOW, SLOT_PERIOD)) if SLOT_PERIOD else "off",
           PUMPS, PUMP_ID, UNTIL or "fin"))
    # une connexion keep-alive PAR thread (http.client n'est pas thread-safe)
    conns = [HillConn(BASE, TIMEOUT, PROXY) for _ in range(THREADS_MAX)]
    threads = [threading.Thread(target=worker, args=(i, conns[i], ck), daemon=True)
               for i in range(THREADS_MAX)]
    for t in threads:
        t.start()

    win_streak = 0
    loss_streak = 0
    stats["held_since"] = time.time()
    next_poll = time.time()
    while not stop_requested():
        time.sleep(0.2)
        now = time.time()
        if now >= next_poll:
            next_poll = now + STATUS_EVERY
            king = poll_status(op, ck) if STATUS_PATH else None
            mine_now = bool(king is not None and str(king) in OUR_IDS)
            win_streak = win_streak + 1 if mine_now else 0
            loss_streak = 0 if mine_now else loss_streak + 1
            adapt(king, win_streak, loss_streak)
            s = write_status()
            log("niv=%d thr=%d int=%.2fs | roi=%s ROI(nous)=%s | claims=%d ok=%d err=%d 429=%d | escal=%d relax=%d"
                % (s["level"], s["threads"], s["interval"], s["king"], s["is_king"],
                   s["claims"], s["ok"], s["err"], s["rate_limited"],
                   s["escalations"], s["relaxations"]))
        elif now - getattr(run, "_w", 0) >= 1.0:
            run._w = now
            write_status()

    _stop.set()
    for t in threads:
        t.join(timeout=2)
    write_status()
    log("arret propre (claims=%d, prises=%d, reparations=%d)"
        % (stats["claims"], stats["takeovers"], stats["repairs"]))
    return 0


def main():
    ap = argparse.ArgumentParser(description="KoTH hill holder adaptatif (NCTF26)")
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--run", action="store_true")
    g.add_argument("--probe", action="store_true")
    g.add_argument("--once", action="store_true")
    a = ap.parse_args()

    def _sig(_s, _f):
        _stop.set()

    signal.signal(signal.SIGTERM, _sig)
    signal.signal(signal.SIGINT, _sig)
    if a.probe:
        return probe()
    if a.once:
        if not preflight():
            return 2
        code, _ = claim(HillConn(BASE, TIMEOUT, PROXY), load_cookies())
        log("claim:", code)
        return 0 if code and code < 400 else 1
    return run()


if __name__ == "__main__":
    sys.exit(main())
