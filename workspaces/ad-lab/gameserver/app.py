#!/usr/bin/env python3
"""ad-lab gameserver — minimal mock of a CTF A&D scoring endpoint.

Only what submitter.py / sla_monitor.py need to be tested against:
- POST /submit {"flag": "..."} -> accept/reject based on a simple regex and
  dedup, mimicking a real gameserver's response shape.
- GET /health -> 200 for sla_monitor.py's check_http().
"""
import re
import time

from flask import Flask, jsonify, request

app = Flask(__name__)

FLAG_RE = re.compile(r"NCTF\{[^}]+\}")
_accepted = set()


@app.get("/health")
def health():
    return jsonify(ok=True)


@app.post("/submit")
def submit():
    data = request.get_json(silent=True) or {}
    flag = data.get("flag", "")
    if not FLAG_RE.fullmatch(flag):
        return jsonify(status="invalid_format"), 400
    if flag in _accepted:
        return jsonify(status="already_submitted"), 208
    _accepted.add(flag)
    return jsonify(status="accepted", points=10, ts=time.time()), 200


@app.get("/stats")
def stats():
    return jsonify(accepted_count=len(_accepted), accepted=sorted(_accepted))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=9090)
