#!/usr/bin/env python3
"""Archive le TEXTE des pages de regles/sections d'arena.ctf.tg (NCTF26) via le
navigateur headless (Playwright), en reutilisant la session sauvegardee par
nctf26_client.py (nctf26_storage_state.json). Lecture seule: aucune soumission,
aucun clic d'action -- on ne fait que naviguer et extraire innerText.

Usage: python3 src/tools/ctf/nctf26_archive_rules.py [out_dir]
Sortie par defaut: workspaces/nctf26-finale/platform-rules/<section>.txt + nav.json
"""
from __future__ import annotations
import json, sys, re
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE_URL = "https://arena.ctf.tg"
HERE = Path(__file__).parent
STATE_FILE = HERE / "nctf26_storage_state.json"
RESOLVE = ["--host-resolver-rules=MAP arena.ctf.tg 104.21.67.127"]

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else (
    HERE.parent.parent.parent / "workspaces" / "nctf26-finale" / "platform-rules")

def slug(s: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s.strip().lower()).strip("-")
    return s or "page"

def main():
    if not STATE_FILE.exists():
        print("Pas de session -- lancer 'nctf26_client.py login' d'abord.", file=sys.stderr)
        sys.exit(2)
    OUT.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=RESOLVE)
        ctx = browser.new_context(storage_state=str(STATE_FILE))
        page = ctx.new_page()
        page.goto(BASE_URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2000)
        if "login" in page.url:
            print("Session expiree (redirige vers /login) -- relancer login.", file=sys.stderr)
            sys.exit(3)

        # Recupere les liens du menu de navigation (header)
        links = page.eval_on_selector_all(
            "nav a[href], header a[href], .navbar a[href]",
            "els => els.map(e => ({text: e.innerText.trim(), href: e.href}))")
        # dedup + ne garde que les pages internes informatives
        seen, nav = set(), []
        for l in links:
            h = l["href"].split("#")[0]
            if not h.startswith(BASE_URL):
                continue
            if h in seen:
                continue
            seen.add(h)
            nav.append({"text": l["text"], "href": h})
        (OUT / "nav.json").write_text(json.dumps(nav, ensure_ascii=False, indent=2))
        print(f"[nav] {len(nav)} liens internes -> {OUT/'nav.json'}")

        # Sections dont on veut archiver le texte (match sur le libelle)
        want = ("accès", "acces", "défense", "defense", "koth", "support",
                "instances", "scoreboard", "règl", "regl", "accueil", "home")
        targets = [n for n in nav if any(w in n["text"].lower() for w in want)]
        # toujours inclure la home et la page koth connue
        extra = [{"text": "accueil", "href": BASE_URL + "/"},
                 {"text": "koth", "href": BASE_URL + "/plugins/koth/"}]
        for e in extra:
            if e["href"] not in seen:
                targets.append(e); seen.add(e["href"])

        for t in targets:
            try:
                page.goto(t["href"], wait_until="domcontentloaded", timeout=45000)
                page.wait_for_timeout(1500)
                txt = page.inner_text("body")
                name = slug(t["text"] or t["href"].rsplit("/", 1)[-1])
                fp = OUT / f"{name}.txt"
                fp.write_text(f"# {t['text']}  <{t['href']}>\n# archivé via headless {page.url}\n\n{txt}\n")
                print(f"[ok] {t['text']:<14} {len(txt):>6} chars -> {fp.name}")
            except Exception as ex:
                print(f"[skip] {t['text']} ({t['href']}): {ex}", file=sys.stderr)
        browser.close()

if __name__ == "__main__":
    main()
