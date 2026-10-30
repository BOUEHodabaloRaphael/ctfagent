#!/usr/bin/env python3
"""
Capture live (via tshark, déjà installé) le trafic entrant sur tes ports de
service, et flag les payloads qui matchent des patterns d'injection
courants — pour repérer vite ce que les autres équipes essaient sur toi
et patcher en conséquence.

Usage : sudo python3 pcap_watch.py --iface tun0 --ports 8080,1337
        (sudo requis pour la capture live, comme tshark en général)
"""
import argparse
import re
import subprocess
import sys
from datetime import datetime

SUSPECT_PATTERNS = [
    (re.compile(rb"UNION\s+SELECT", re.I), "SQLi (UNION SELECT)"),
    (re.compile(rb"' OR ", re.I), "SQLi (OR bypass)"),
    (re.compile(rb"<script", re.I), "XSS"),
    (re.compile(rb"\.\./"), "Path traversal"),
    (re.compile(rb"\$\{jndi:"), "Log4Shell-style JNDI"),
    (re.compile(rb"__proto__|constructor\[.prototype"), "Prototype pollution"),
    (re.compile(rb"os\.system|subprocess\.|eval\(|exec\("), "Code injection (py-ish)"),
    (re.compile(rb"%00"), "Null byte injection"),
    (re.compile(rb"AAAAAAAAAAAAAAAA"), "Probable buffer overflow (padding)"),
]

ALERT_LOG = "alerts.log"


def log_alert(line: str):
    ts = datetime.now().strftime("%H:%M:%S")
    entry = f"[{ts}] {line}"
    print(entry, flush=True)
    with open(ALERT_LOG, "a") as f:
        f.write(entry + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--iface", required=True, help="ex: tun0, eth0")
    ap.add_argument("--ports", required=True, help="ports de tes services, ex: 8080,1337")
    args = ap.parse_args()

    port_filter = " or ".join(f"tcp.port=={p}" for p in args.ports.split(","))
    cmd = [
        "tshark", "-i", args.iface, "-Y", port_filter,
        "-T", "fields", "-e", "ip.src", "-e", "tcp.srcport", "-e", "data.text",
        "-l",
    ]

    print(f"tshark: {' '.join(cmd)}")
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        sys.exit("[!] tshark introuvable.")

    print(f"Watching iface={args.iface} ports={args.ports}. Alertes -> {ALERT_LOG}. Ctrl+C pour arrêter.")
    for raw in proc.stdout:
        parts = raw.rstrip(b"\n").split(b"\t")
        if len(parts) < 3 or not parts[2]:
            continue
        src, sport, payload = parts[0], parts[1], parts[2]
        for pattern, label in SUSPECT_PATTERNS:
            if pattern.search(payload):
                snippet = payload[:120].decode(errors="replace")
                log_alert(f"{label} depuis {src.decode()}:{sport.decode()} -> {snippet!r}")
                break


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
