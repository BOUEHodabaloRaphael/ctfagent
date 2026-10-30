#!/usr/bin/env python3
"""Client headless (Playwright) pour arena.ctf.tg (NCTF26 - CERT.tg).

Verifie et pret: le site est accessible via Chromium headless sans blocage
anti-bot (teste le 2026-10-30, statuts 200 sur ctf.tg/arena.ctf.tg/login/tos).
Le site est derriere Cloudflare (cookie cf_clearance pose) -> un client HTTP
brut (requests) sera probablement bloque, Playwright est necessaire.

Formulaire de login confirme: champs 'name' (username/email), 'password',
'nonce' (CSRF cache a relire a chaque chargement de page, PAS a coder en dur).

PAS ENCORE TESTE (nécessite un compte, pas encore créé au 2026-10-30):
- le flux de login reel (POST + redirection)
- la structure de la page /challenges (liste, categories, formulaire de
  soumission de flag -- noms de champs exacts a confirmer une fois connecté)
- l'endpoint/mecanisme exact de soumission de flag

Usage prevu (une fois le compte cree, ne jamais committer les creds en dur --
passer par variables d'environnement) :
    NCTF_USER=... NCTF_PASS=... python3 nctf26_client.py login
    NCTF_USER=... NCTF_PASS=... python3 nctf26_client.py list
    NCTF_USER=... NCTF_PASS=... python3 nctf26_client.py submit <challenge_id> "NCTF{...}"

Regle NCTF26 a respecter strictement (reglement art. 7): pas de bruteforce de
soumission, pas de depassement du rate-limit de la plateforme. Ce script ne
retente jamais automatiquement un flag refuse -- une seule soumission par
appel, confirmee par l'utilisateur avant chaque flag important.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright, Page

BASE_URL = "https://arena.ctf.tg"
STATE_FILE = Path(__file__).parent / "nctf26_storage_state.json"


def get_nonce(page: Page) -> str:
    """Relit le champ nonce (CSRF) depuis la page actuelle -- ne jamais
    reutiliser une valeur mise en cache, il change a chaque chargement."""
    el = page.query_selector("input[name='nonce']")
    if el is None:
        raise RuntimeError("Champ nonce introuvable sur la page -- structure du site a peut-etre change")
    return el.get_attribute("value") or ""


def login(headless: bool = True) -> None:
    user = os.environ.get("NCTF_USER")
    password = os.environ.get("NCTF_PASS")
    if not user or not password:
        print("Definir NCTF_USER et NCTF_PASS (variables d'environnement, jamais en dur dans le code).", file=sys.stderr)
        sys.exit(1)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        page = browser.new_page()
        page.goto(f"{BASE_URL}/login", wait_until="networkidle")

        nonce = get_nonce(page)
        page.fill("input[name='name']", user)
        page.fill("input[name='password']", password)
        # Le champ nonce est deja rempli par le serveur, pas besoin de le re-remplir
        page.click("input[name='_submit']")
        page.wait_for_load_state("networkidle")

        if "login" in page.url:
            print(f"ECHEC login probable (toujours sur {page.url}) -- verifier creds/MFA/nonce.", file=sys.stderr)
            # Sauver un screenshot pour diagnostic
            page.screenshot(path=str(Path(__file__).parent / "login_debug.png"))
            sys.exit(1)

        print(f"Login OK, redirige vers {page.url}")
        page.context.storage_state(path=str(STATE_FILE))
        print(f"Session sauvegardee dans {STATE_FILE}")
        browser.close()


def _authenticated_page(p, headless: bool = True) -> tuple:
    if not STATE_FILE.exists():
        print("Pas de session sauvegardee -- lancer 'login' d'abord.", file=sys.stderr)
        sys.exit(1)
    browser = p.chromium.launch(headless=headless)
    context = browser.new_context(storage_state=str(STATE_FILE))
    page = context.new_page()
    return browser, page


def list_challenges() -> None:
    with sync_playwright() as p:
        browser, page = _authenticated_page(p)
        page.goto(f"{BASE_URL}/challenges", wait_until="networkidle")
        # Structure exacte a confirmer une fois le compte cree -- ceci est
        # un point de depart, pas une implementation finale.
        print(f"URL finale: {page.url}")
        print(page.content()[:2000])
        browser.close()


def submit_flag(challenge_id: str, flag: str) -> None:
    """Soumet UN SEUL flag pour UN SEUL challenge. Pas de boucle, pas de
    retry automatique -- conforme au reglement anti-bruteforce (art. 7)."""
    with sync_playwright() as p:
        browser, page = _authenticated_page(p)
        page.goto(f"{BASE_URL}/challenges/{challenge_id}", wait_until="networkidle")
        print(f"Page chargee: {page.url}")
        print("STRUCTURE DE SOUMISSION NON ENCORE CONFIRMEE -- inspecter la page")
        print("manuellement (ou via read_page) avant d'automatiser cette etape.")
        print(f"Flag preparer pour soumission (PAS ENCORE ENVOYE): {flag}")
        browser.close()


def main():
    ap = argparse.ArgumentParser(description="Client NCTF26 (arena.ctf.tg)")
    ap.add_argument("action", choices=["login", "list", "submit"])
    ap.add_argument("challenge_id", nargs="?")
    ap.add_argument("flag", nargs="?")
    args = ap.parse_args()

    if args.action == "login":
        login()
    elif args.action == "list":
        list_challenges()
    elif args.action == "submit":
        if not args.challenge_id or not args.flag:
            print("Usage: submit <challenge_id> <flag>", file=sys.stderr)
            sys.exit(1)
        submit_flag(args.challenge_id, args.flag)


if __name__ == "__main__":
    main()
