#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NCTF26 FINALE — recon KoTH (headless, reutilise la session du client).
À LANCER À L'OUVERTURE (t+0) pour decouvrir, SANS deviner :
  - les vrais endpoints API de la colline (claim/status) en observant le trafic
    XHR/fetch que la page KOTH emet elle-meme ;
  - notre identifiant d'equipe + les IP d'instances (page /team, "Mes instances").
→ de quoi remplir  hill.env  en 1 minute, puis lancer koth_run.sh.

Ne CLIQUE rien d'offensif : il observe seulement. (Le premier claim se fait
ensuite via hill_hold.py / koth_run.sh.)

USAGE :  python3 recon_koth.py            # dump KOTH + team + instances
         python3 recon_koth.py /plugins/koth/   # page de depart custom
"""
import sys, json, re
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:
    print("playwright manquant : pip3 install playwright && playwright install chromium", file=sys.stderr)
    sys.exit(1)

BASE = "https://arena.ctf.tg"
STATE = Path(__file__).parent.parent / "nctf26_storage_state.json"
LAUNCH_ARGS = ["--host-resolver-rules=MAP arena.ctf.tg 104.21.67.127"]

PAGES = ["/plugins/koth/", "/team", "/challenges"]  # ajoute "Mes instances" si URL connue

def main():
    if len(sys.argv) > 1:
        PAGES.insert(0, sys.argv[1])
    if not STATE.exists():
        print("Pas de session (nctf26_storage_state.json). Rafraichir d'abord.", file=sys.stderr)
        sys.exit(1)

    api_hits = []   # (method, url, post_body)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=LAUNCH_ARGS)
        ctx = browser.new_context(storage_state=str(STATE))
        page = ctx.new_page()

        def on_request(req):
            u = req.url
            # on ne garde que les appels d'API (pas les assets)
            if any(k in u for k in ("/api", "/koth", "claim", "status", "king", "hill")) \
               and not u.endswith((".js", ".css", ".png", ".svg", ".woff2", ".ico")):
                body = None
                try:
                    body = req.post_data
                except Exception:
                    pass
                api_hits.append((req.method, u, body))
        page.on("request", on_request)

        for path in PAGES:
            try:
                page.goto(BASE + path, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(4000)  # laisser la page poller son API
                txt = page.inner_text("body")[:2500]
                print("\n" + "=" * 70)
                print(f"PAGE {path}  ->  {page.url}")
                print("=" * 70)
                print(txt)
                # indices : identifiants d'equipe / token / IP d'instances
                for m in set(re.findall(r"\b(?:10|172|192)\.\d+\.\d+\.\d+(?::\d+)?\b", txt)):
                    print("  [IP?]", m)
                for m in set(re.findall(r"\b[0-9a-f]{16,}\b", txt)):
                    print("  [token/hex?]", m)
            except Exception as e:
                print(f"\n[PAGE {path}] erreur: {e}")

        print("\n" + "#" * 70)
        print("# APPELS API OBSERVES (candidats claim/status) :")
        print("#" * 70)
        seen = set()
        for meth, url, body in api_hits:
            key = (meth, url.split("?")[0])
            if key in seen:
                continue
            seen.add(key)
            rel = url.replace(BASE, "")
            print(f"{meth:5s} {rel}" + (f"   body={body[:160]}" if body else ""))
        print("\n→ Reporter claim/status dans hill.env (KOTH_CLAIM_PATH/METHOD/BODY, KOTH_STATUS_PATH),")
        print("  KOTH_OUR_ID = notre identifiant d'equipe, puis : bash koth_run.sh")
        browser.close()

if __name__ == "__main__":
    main()
