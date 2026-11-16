#!/usr/bin/env python3
"""
Soumission de flags, générique (HTTP JSON ou socket TCP texte selon config).
Dédup locale pour ne jamais renvoyer un flag déjà soumis (certaines
plateformes pénalisent/rate-limit les doublons).

Usage standalone : echo FLAG{...} | python3 submitter.py
"""
import sys
import socket
import re
from pathlib import Path

import requests

import config

SEEN_PATH = Path(__file__).parent / "submitted_flags.txt"


def _load_seen() -> set:
    if not SEEN_PATH.exists():
        return set()
    return set(SEEN_PATH.read_text().splitlines())


def _mark_seen(flag: str):
    with SEEN_PATH.open("a") as f:
        f.write(flag + "\n")


class FlagSubmitter:
    def __init__(self):
        self.seen = _load_seen()
        self.flag_re = re.compile(config.FLAG_REGEX)

    def extract(self, text: str) -> list[str]:
        return self.flag_re.findall(text)

    def submit(self, flags: list[str]) -> dict:
        """Soumet chaque flag non-déjà-vu. Retourne {flag: result_str}.

        Un flag n'est marqué "déjà soumis" (et donc jamais re-soumis) QUE si la
        soumission a effectivement abouti. Une erreur transport (timeout, reset),
        un HTTP 5xx, ou un marqueur transitoire configuré (config.SUBMIT_RETRY_SUBSTRINGS)
        laissent le flag NON-vu → il sera réessayé au tick suivant. Sans ça, un
        simple timeout faisait perdre définitivement un flag valide en A/D.
        """
        results = {}
        for flag in flags:
            if flag in self.seen:
                continue
            retryable = False
            try:
                if config.SUBMIT_TCP_HOST:
                    result = self._submit_tcp(flag)
                else:
                    result = self._submit_http(flag)
            except Exception as e:
                result = f"ERROR: {e}"
                retryable = True  # échec transport → réessayer au prochain tick
            else:
                retryable = self._is_retryable(result)
            results[flag] = result
            if not retryable:
                self.seen.add(flag)
                _mark_seen(flag)
        return results

    @staticmethod
    def _is_retryable(result: str) -> bool:
        """Vrai si la réponse indique un échec transitoire (à re-soumettre),
        pas un rejet définitif (flag invalide/expiré/own-flag, qu'on marque vu)."""
        head = result.split(" ", 1)[0]
        if head.isdigit() and 500 <= int(head) <= 599:  # HTTP 5xx côté scoreboard
            return True
        low = result.lower()
        return any(s.lower() in low for s in getattr(config, "SUBMIT_RETRY_SUBSTRINGS", []))

    def _submit_http(self, flag: str) -> str:
        # Forme de la valeur: scalaire par defaut, ou liste si la plateforme
        # l'exige (ex. ICC: {"flags": ["<flag>"]}). getattr -> compat anciens config.
        value = [flag] if getattr(config, "SUBMIT_JSON_VALUE_LIST", False) else flag
        r = requests.request(
            config.SUBMIT_METHOD,
            config.SUBMIT_URL,
            json={config.SUBMIT_JSON_KEY: value},
            headers=config.SUBMIT_HEADERS,
            timeout=config.SUBMIT_TIMEOUT,
        )
        return f"{r.status_code} {r.text[:200]}"

    def _submit_tcp(self, flag: str) -> str:
        with socket.create_connection(
            (config.SUBMIT_TCP_HOST, config.SUBMIT_TCP_PORT), timeout=config.SUBMIT_TIMEOUT
        ) as s:
            s.sendall((flag + "\n").encode())
            return s.recv(1024).decode(errors="replace").strip()


if __name__ == "__main__":
    submitter = FlagSubmitter()
    text = sys.stdin.read()
    flags = submitter.extract(text)
    if not flags:
        print("Aucun flag reconnu par FLAG_REGEX dans l'entrée.", file=sys.stderr)
        sys.exit(1)
    for flag, result in submitter.submit(flags).items():
        print(f"{flag} -> {result}")
