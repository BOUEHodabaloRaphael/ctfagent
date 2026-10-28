#!/usr/bin/env python3
"""Read-only session/state check for the bugpwn CTFd platform.
No flag submission, no exploitation. Logs to session_check.txt."""
import glob, json, os, re, sys
from datetime import datetime, timezone
import requests

BASE = "https://ctf.bugpwn.com"
HERE = os.path.dirname(os.path.abspath(__file__))
STATE = os.path.join(HERE, "session", "storage_state.json")
LOG = os.path.join(HERE, "session_check.txt")
USER = os.environ.get("CTF_USER", "L&_M@z4rt")
PASS = os.environ.get("CTF_PASS", "")  # export CTF_PASS=... (avoid hardcoding)
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) session-check"}


def log(msg=""):
    line = f"[{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}] {msg}"
    print(line)
    with open(LOG, "a") as f:
        f.write(line + "\n")


def init_data(html):
    m = re.search(r"'userId':\s*(\d+).*?'userName':\s*(null|\"[^\"]*\")", html, re.S)
    return (int(m.group(1)), m.group(2).strip('"')) if m else (None, None)


def new_session():
    s = requests.Session()
    s.headers.update(UA)
    return s


def load_state(s):
    if not os.path.exists(STATE):
        return False
    for c in json.load(open(STATE)).get("cookies", []):
        s.cookies.set(c["name"], c["value"], domain=c["domain"], path=c.get("path", "/"))
    return True


def logged_in(s):
    r = s.get(f"{BASE}/challenges", allow_redirects=False, timeout=20)
    if r.status_code in (301, 302, 303):
        return False, r.headers.get("Location")
    uid, name = init_data(r.text)
    return bool(uid), f"HTTP {r.status_code} userId={uid} userName={name}"


def fresh_login(s):
    if not PASS:
        log("No CTF_PASS in env -> cannot do fresh login")
        return False
    r = s.get(f"{BASE}/login", timeout=20)
    nonce = re.search(r'name="nonce"[^>]*value="([^"]+)"', r.text) or re.search(r'value="([0-9a-f]{64})"', r.text)
    r = s.post(f"{BASE}/login", data={"name": USER, "password": PASS, "nonce": nonce.group(1) if nonce else "", "_submit": "Submit"},
               allow_redirects=False, timeout=20)
    log(f"Fresh login POST -> HTTP {r.status_code} Location={r.headers.get('Location')}")
    return r.status_code in (301, 302, 303) and "login" not in (r.headers.get("Location") or "")


def api(s, path):
    r = s.get(f"{BASE}/api/v1{path}", timeout=20)
    try:
        return r.json()
    except Exception:
        return {"success": False, "http": r.status_code}


def main():
    log("=== session check start ===")
    s = new_session()
    r = s.get(BASE, timeout=20)
    title = re.search(r"<title>(.*?)</title>", r.text, re.S)
    log(f"Home: HTTP {r.status_code}, title={title.group(1).strip() if title else None}, {len(r.text)} bytes, server={r.headers.get('server')}")
    if r.status_code != 200:
        log("Platform not healthy, stopping."); return 1

    used = load_state(s)
    log(f"storage_state.json loaded: {used}")
    ok, info = logged_in(s)
    log(f"/challenges logged in: {ok} ({info})")
    if not ok:
        s = new_session()
        if fresh_login(s):
            ok, info = logged_in(s)
            log(f"After fresh login: {ok} ({info})")
        if not ok:
            log("Still not authenticated."); return 2

    # competition timer / state
    page = s.get(f"{BASE}/challenges", timeout=20).text
    for k in ("ctfStart", "ctfEnd", "start", "end"):
        m = re.search(rf"'{k}':\s*([^,\n]+)", page)
        if m: log(f"init.{k} = {m.group(1).strip()}")
    cfg = api(s, "/challenges")
    log(f"/api/v1/challenges success={cfg.get('success')}")
    if not cfg.get("success"):
        log(f"Challenges API says: {json.dumps(cfg)[:300]} (competition paused/ended?)")
    chals = cfg.get("data", [])
    log(f"Published challenges: {len(chals)}")

    # diff against latest saved snapshot
    prev_files = sorted(glob.glob(os.path.join(HERE, "artifacts", "challenges_*.json")))
    prev_ids = set()
    if prev_files:
        prev = json.load(open(prev_files[-1]))
        prev_ids = {c["id"] for c in prev.get("challenges", [])}
        log(f"Baseline snapshot: {os.path.basename(prev_files[-1])} ({len(prev_ids)} challenges)")
    for c in sorted(chals, key=lambda c: c["id"]):
        tag = "NEW " if prev_ids and c["id"] not in prev_ids else "    "
        log(f"  {tag}#{c['id']} {c['name']!r} [{c.get('category')}] {c['value']}pts solves={c['solves']} solved_by_me={c.get('solved_by_me')}")

    me = api(s, "/users/me").get("data", {})
    log(f"Me: id={me.get('id')} name={me.get('name')} score={me.get('score')} place={me.get('place')}")
    sb = api(s, "/scoreboard").get("data", [])
    log(f"Scoreboard entries: {len(sb)}; top 5:")
    for e in sb[:5]:
        log(f"  {e['pos']}. {e['name']} {e['score']}")
    mine = [e for e in sb if e.get("name") == me.get("name")]
    if mine: log(f"My position: {mine[0]['pos']} / {len(sb)} with {mine[0]['score']} pts")
    log("=== session check end ===")
    return 0


if __name__ == "__main__":
    sys.exit(main())
