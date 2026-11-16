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
        browser = p.chromium.launch(headless=headless, args=["--host-resolver-rules=MAP arena.ctf.tg 104.21.67.127"])
        page = browser.new_page()
        page.goto(f"{BASE_URL}/login", wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(1500)

        nonce = get_nonce(page)
        page.fill("input[name='name']", user)
        page.fill("input[name='password']", password)
        # Le champ nonce est deja rempli par le serveur, pas besoin de le re-remplir
        page.click("input[name='_submit']")
        # networkidle ne se declenche jamais pendant l'evenement live (polling
        # continu du cote plateforme) -- attendre un chargement simple + delai fixe.
        page.wait_for_load_state("domcontentloaded", timeout=45000)
        page.wait_for_timeout(1500)

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
    browser = p.chromium.launch(headless=headless, args=["--host-resolver-rules=MAP arena.ctf.tg 104.21.67.127"])
    context = browser.new_context(storage_state=str(STATE_FILE))
    page = context.new_page()
    return browser, page


def list_challenges() -> None:
    with sync_playwright() as p:
        browser, page = _authenticated_page(p)
        page.goto(f"{BASE_URL}/challenges", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2000)
        # Structure exacte a confirmer une fois le compte cree -- ceci est
        # un point de depart, pas une implementation finale.
        print(f"URL finale: {page.url}")
        print(page.content()[:4000])
        browser.close()


def submit_flag(challenge_name: str, flag: str) -> None:
    """Soumet UN SEUL flag pour UN SEUL challenge. Pas de boucle, pas de
    retry automatique -- conforme au reglement anti-bruteforce (art. 7).

    challenge_name: le nom affiche du challenge tel qu'il apparait sur la
    carte (ex: 'uart-capture', 'algorithme123--tisserands-dapaong'). Le
    theme (hibris) ouvre une modale via un bouton (pas de navigation vers
    /challenges/<id>), donc on clique le bouton correspondant sur la page
    /challenges plutot que de naviguer directement.
    """
    with sync_playwright() as p:
        browser, page = _authenticated_page(p)
        page.goto(f"{BASE_URL}/challenges", wait_until="domcontentloaded", timeout=60000)
        page.wait_for_timeout(2000)

        # Le bouton de challenge contient le nom en texte (parfois avec les
        # points dans un span separe) -- on cherche un bouton dont le texte
        # contient exactement le nom demande.
        btn = page.get_by_role("button", name=challenge_name, exact=False).first
        btn.wait_for(state="visible", timeout=10000)
        btn.click()

        flag_input = page.get_by_placeholder("Flag")
        flag_input.wait_for(state="visible", timeout=10000)
        flag_input.fill(flag)

        submit_btn = page.get_by_role("button", name="Submit")
        submit_btn.click()

        # Le resultat (Correct/Incorrect) apparait comme une alerte/notice
        # dans la modale -- on attend un court instant puis on capture le
        # texte visible le plus pertinent.
        page.wait_for_timeout(2000)
        result_text = None
        for sel in ["[role=alert]", ".alert", ".notice", ".toast"]:
            el = page.query_selector(sel)
            if el:
                txt = el.inner_text().strip()
                if txt:
                    result_text = txt
                    break
        print(f"Challenge: {challenge_name}")
        print(f"Flag soumis: {flag}")
        print(f"Resultat: {result_text!r}")
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
