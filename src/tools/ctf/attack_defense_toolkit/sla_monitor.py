#!/usr/bin/env python3
"""
Surveille en continu tes propres services (config.SERVICES) pour détecter
une panne AVANT que le SLA checker officiel ne te pénalise (souvent trop
tard pour réagir sinon, vu le tick de 90-120s). Alerte terminal + bip +
notify-send si dispo.

Usage : python3 sla_monitor.py [--interval 15]
"""
import argparse
import socket
import subprocess
import time
from datetime import datetime

import requests

import config

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def check_tcp(host: str, port: int, timeout=3) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def check_http(host: str, port: int, timeout=3) -> bool:
    try:
        r = requests.get(f"http://{host}:{port}/", timeout=timeout)
        return r.status_code < 500
    except requests.RequestException:
        return False


def notify(name: str):
    try:
        subprocess.run(["notify-send", "-u", "critical", f"SERVICE DOWN: {name}"], timeout=2)
    except FileNotFoundError:
        pass
    print("\a", end="", flush=True)  # bip terminal


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=float, default=15.0)
    args = ap.parse_args()

    if not config.SERVICES:
        raise SystemExit("[!] config.SERVICES est vide, remplis-le d'abord.")

    state = {name: True for name, *_ in config.SERVICES}

    print(f"Monitoring {len(config.SERVICES)} service(s), check toutes les {args.interval}s. Ctrl+C pour arrêter.")
    while True:
        ts = datetime.now().strftime("%H:%M:%S")
        for name, host, port, kind in config.SERVICES:
            ok = check_http(host, port) if kind == "http" else check_tcp(host, port)
            was_ok = state[name]
            if ok:
                color = GREEN
                status = "UP"
            else:
                color = RED
                status = "DOWN"
            print(f"[{ts}] {color}{name:<20} {status}{RESET}")
            if was_ok and not ok:
                notify(name)
            state[name] = ok
        time.sleep(args.interval)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
