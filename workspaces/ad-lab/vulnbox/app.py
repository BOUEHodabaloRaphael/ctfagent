#!/usr/bin/env python3
"""ad-lab vulnbox — minimal A&D practice service.

Deliberately vulnerable (command injection in /ping) to validate the
attack_defense_toolkit end-to-end: exploit_runner.py must be able to steal
the current flag from a black-box IP, on a loop, the same way it would
against a real competition service.

The flag rotates every FLAG_ROTATE_SECONDS, mimicking a real A&D tick where
the SLA checker publishes a fresh flag ID/value periodically.
"""
import os
import re
import secrets
import subprocess
import threading
import time

from flask import Flask, request

app = Flask(__name__)

FLAG_ROTATE_SECONDS = int(os.environ.get("FLAG_ROTATE_SECONDS", "30"))
_state = {"flag": None}
_lock = threading.Lock()


def _new_flag() -> str:
    return f"NCTF{{labtest_{secrets.token_hex(8)}}}"


def _rotator():
    while True:
        with _lock:
            _state["flag"] = _new_flag()
            # Keep it on disk too, like a real checker would seed /flag.txt
            with open("/flag.txt", "w") as fh:
                fh.write(_state["flag"] + "\n")
        time.sleep(FLAG_ROTATE_SECONDS)


threading.Thread(target=_rotator, daemon=True).start()


@app.get("/")
def index():
    return "ad-lab vulnbox — ping service. Try /ping?host=127.0.0.1\n"


@app.get("/health")
def health():
    return {"ok": True}, 200


@app.get("/ping")
def ping():
    """Intentionally vulnerable: the 'host' param is shell-interpolated.

    This is the one bug exploit_runner.py's exploit module must find and
    abuse, e.g.:  /ping?host=127.0.0.1;cat /flag.txt
    """
    host = request.args.get("host", "127.0.0.1")
    # Deliberately naive: no sanitization, shell=True, string concatenation.
    cmd = f"ping -c 1 -W 1 {host}"
    try:
        out = subprocess.run(
            cmd, shell=True, capture_output=True, timeout=5, text=True
        ).stdout
    except Exception as e:
        out = f"error: {e}"
    return out, 200, {"Content-Type": "text/plain"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
