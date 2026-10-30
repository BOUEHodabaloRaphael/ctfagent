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
        """Soumet chaque flag non-déjà-vu. Retourne {flag: result_str}."""
        results = {}
        for flag in flags:
            if flag in self.seen:
                continue
            try:
                if config.SUBMIT_TCP_HOST:
                    result = self._submit_tcp(flag)
                else:
                    result = self._submit_http(flag)
            except Exception as e:
                result = f"ERROR: {e}"
            results[flag] = result
            self.seen.add(flag)
            _mark_seen(flag)
        return results

    def _submit_http(self, flag: str) -> str:
        r = requests.request(
            config.SUBMIT_METHOD,
            config.SUBMIT_URL,
            json={config.SUBMIT_JSON_KEY: flag},
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
