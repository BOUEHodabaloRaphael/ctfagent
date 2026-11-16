#!/usr/bin/env python3
"""Essai KOTH borné : simulation par défaut, jamais de rafale ni de relance.

Utilisation uniquement sur une colline CTF autorisée, selon son règlement.
Le protocole HMAC reproduit le script joint ; il n'a pas été testé sur le serveur.
La période est une hypothèse, la marge un paramètre d'essai, pas une mesure validée.
Voir README.md pour les limites et la configuration.
"""
from __future__ import annotations

import argparse
import hashlib
import hmac
import json
import math
import multiprocessing as mp
import os
from pathlib import Path
import time
import urllib.error
import urllib.parse
import urllib.request

MAX_CLAIMS = 12
MAX_DURATION_S = 420.0
NETWORK_TIMEOUT_S = 5.0


def finite_float(value: str) -> float:
    result = float(value)
    if not math.isfinite(result):
        raise argparse.ArgumentTypeError("Le nombre doit être fini.")
    return result


def next_slot(now: float, anchor_local: float, period: float, margin: float):
    """Choisir un créneau dont l'heure de départ est strictement future."""
    k = max(0, math.floor((now + margin - anchor_local) / period) + 1)
    tick = anchor_local + k * period
    return tick, tick - margin


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Ne jamais transmettre le payload de claim à une autre URL.
        return None


def request_worker(connection, config):
    """Une seule requête, sans retry ; processus isolé pour borner sa durée."""
    started = time.time()
    result = {"request_start": started, "http_status": None}
    try:
        # Même encodage que b"..." dans le script d'origine : PAS fromhex().
        key = config["key"].encode("utf-8")
        ts = int(started + config["clock_offset"])
        message = f'{config["team"]}|{ts}'.encode("utf-8")
        sig = hmac.new(key, message, hashlib.sha1).hexdigest()
        payload = json.dumps({"team": config["team"], "ts": ts, "sig": sig}).encode()
        req = urllib.request.Request(
            config["url"], data=payload,
            headers={"Content-Type": "application/json"}, method="POST",
        )
        # Éviter un proxy hérité et interdire les redirections.
        opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({}), NoRedirect()
        )
        try:
            with opener.open(req, timeout=config["timeout"]) as response:
                result["http_status"] = response.status
                result["response_bytes_read"] = len(response.read(8192))
        except urllib.error.HTTPError as exc:
            result["http_status"] = exc.code
            exc.close()
    except Exception as exc:
        # Ne pas journaliser de secrets ni le corps de la réponse.
        result["error_type"] = type(exc).__name__
    finally:
        result["request_end"] = time.time()
        try:
            connection.send(result)
        finally:
            connection.close()


def run_one_request(config, budget: float):
    """Timeout global : aucun second POST si la première tentative tarde."""
    ctx = mp.get_context("spawn")
    receiver, sender = ctx.Pipe(duplex=False)
    process = ctx.Process(target=request_worker, args=(sender, config))
    start = time.monotonic()
    try:
        process.start()
        sender.close()
        process.join(max(0.0, budget - (time.monotonic() - start)))
        if process.is_alive():
            process.terminate()
            process.join(0.2)
            if process.is_alive():
                process.kill()
                process.join(0.2)
            return {"http_status": None, "error_type": "GlobalTimeout"}
        if receiver.poll():
            try:
                return receiver.recv()
            except EOFError:
                pass
        return {"http_status": None, "error_type": "WorkerFailure"}
    finally:
        if process.is_alive():
            process.terminate()
            process.join(0.2)
            if process.is_alive():
                process.kill()
                process.join(0.2)
        receiver.close()
        sender.close()


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--anchor", type=finite_float, required=True,
                   help="Timestamp serveur RÉCENT d'un événement pertinent pour le scorer.")
    p.add_argument("--period", type=finite_float, default=30.3814,
                   help="Période hypothétique en secondes (défaut : 30.3814).")
    p.add_argument("--margin", type=finite_float, required=True,
                   help="Marge d'essai avant le tick ; pas de calibration automatique.")
    p.add_argument("--clock-offset-s", type=finite_float, default=None,
                   help="Heure serveur moins heure locale ; explicitement requis en exécution.")
    p.add_argument("--claims", type=int, default=3,
                   help="Nombre de tentatives, de 1 à 12 (défaut : 3).")
    p.add_argument("--duration", type=finite_float, default=120,
                   help="Budget en secondes, maximum 420 (défaut : 120).")
    p.add_argument("--max-model-age-s", type=finite_float, default=180,
                   help="Garde de fraîcheur, de 1 à 600 s ; choix prudent, non mesuré.")
    p.add_argument("--log", type=Path,
                   default=Path(__file__).resolve().parent / "timed_claims_log.jsonl")
    p.add_argument("--execute", action="store_true",
                   help="Autoriser les POSTs ; sans ce drapeau, simulation instantanée uniquement.")
    return p


def validate(p, args):
    if not 1 <= args.claims <= MAX_CLAIMS:
        p.error("--claims doit être compris entre 1 et 12.")
    if not 0 < args.duration <= MAX_DURATION_S:
        p.error("--duration doit être supérieur à 0 et au plus 420.")
    if args.period <= 0 or not 0 < args.margin < args.period:
        p.error("La période doit être positive et 0 < marge < période.")
    if not 1 <= args.max_model_age_s <= 600:
        p.error("--max-model-age-s doit être compris entre 1 et 600.")
    if args.execute and args.clock_offset_s is None:
        p.error("Indiquer explicitement --clock-offset-s (0 seulement si justifié).")


def trial(args, config):
    """Horloge monotone pour les délais ; abandon si l'horloge civile saute."""
    offset = args.clock_offset_s or 0.0
    wall0, mono0 = time.time(), time.monotonic()
    deadline = mono0 + args.duration
    anchor_local = args.anchor - offset
    attempted = 0
    stop = "plafond de tentatives atteint"
    args.log.parent.mkdir(parents=True, exist_ok=True)
    with args.log.open("a", encoding="utf-8") as logfile:
        while attempted < args.claims:
            mono_now, wall_now = time.monotonic(), time.time()
            if abs(wall_now - (wall0 + mono_now - mono0)) > 0.25:
                stop = "saut de l'horloge locale ; modèle invalidé"
                break
            model_age = wall_now + offset - args.anchor
            if model_age < -1 or model_age > args.max_model_age_s:
                stop = "ancre future ou trop ancienne ; pas d'extrapolation prolongée"
                break
            tick, fire = next_slot(wall_now, anchor_local, args.period, args.margin)
            wait_s = fire - wall_now
            remaining = deadline - mono_now
            # Ne pas commencer un créneau sans budget pour toute la tentative.
            if wait_s + NETWORK_TIMEOUT_S > remaining:
                stop = "budget insuffisant pour le prochain créneau"
                break
            if model_age + wait_s > args.max_model_age_s:
                stop = "modèle trop ancien au prochain créneau"
                break
            fire_mono = mono_now + wait_s
            while time.monotonic() < fire_mono:
                sleep_left = fire_mono - time.monotonic()
                if sleep_left <= 0:
                    break
                time.sleep(min(0.2, sleep_left))
            mono_now, wall_now = time.monotonic(), time.time()
            if abs(wall_now - (wall0 + mono_now - mono0)) > 0.25:
                stop = "saut de l'horloge locale avant envoi"
                break
            if mono_now >= deadline:
                stop = "budget écoulé avant envoi"
                break
            # Tolérance de réveil : choix opérationnel de 0.1 s, pas une mesure.
            # Aucun rattrapage immédiat d'un départ manqué.
            if wall_now > fire + 0.1:
                print("Créneau manqué : ignoré, aucune requête de rattrapage.")
                continue
            attempted += 1  # Compter même une tentative interrompue/échouée.
            result = run_one_request(config, min(NETWORK_TIMEOUT_S,
                                                 deadline - time.monotonic()))
            record = {
                "attempt": attempted, "predicted_tick_server": tick + offset,
                "scheduled_start_local": fire, "period_hypothesis_s": args.period,
                "trial_margin_s": args.margin, **result,
            }
            logfile.write(json.dumps(record, ensure_ascii=False) + "\n")
            logfile.flush()
            print(json.dumps(record, ensure_ascii=False))
            status = result["http_status"]
            if status == 429:
                stop = "HTTP 429 : arrêt immédiat, sans retry"
                break
            if result.get("error_type") or status is None or not 200 <= status < 300:
                stop = "échec réseau ou HTTP : arrêt prudent, sans retry"
                break
    print(f"FIN : {attempted} tentative(s) ; {stop}.")
    print("HTTP 2xx ne prouve ni possession ni points. Aucun score n'a été vérifié.")


def main():
    p = parser()
    args = p.parse_args()
    validate(p, args)
    offset = args.clock_offset_s or 0.0
    now = time.time()
    model_age = now + offset - args.anchor
    print("Hypothèse de phase non prouvée ; aucune garantie de gain de points.")
    print(f"Âge de l'ancre : {model_age:.1f} s ; marge d'essai : {args.margin:.3f} s.")
    if not args.execute:
        print("SIMULATION : aucun réseau, aucune attente, aucun journal écrit.")
        if args.clock_offset_s is None:
            print("Décalage serveur/local supposé nul pour cette simulation seulement.")
        if model_age < -1 or model_age > args.max_model_age_s:
            print("ATTENTION : l'exécution refuserait cette ancre future ou trop ancienne.")
        cursor = now
        for n in range(1, args.claims + 1):
            tick, fire = next_slot(cursor, args.anchor - offset,
                                   args.period, args.margin)
            if fire - now + NETWORK_TIMEOUT_S > args.duration:
                break
            print(f"[{n}] départ local={fire:.3f} ; tick serveur prédit={tick + offset:.3f}")
            cursor = fire + 0.001
        return
    if model_age < -1 or model_age > args.max_model_age_s:
        p.error("Ancre future ou trop ancienne : utiliser une vraie observation récente.")
    config = {"key": os.environ.get("KOTH_HILL_KEY", ""),
              "team": os.environ.get("KOTH_TEAM", ""),
              "url": os.environ.get("KOTH_URL", ""),
              "clock_offset": offset, "timeout": NETWORK_TIMEOUT_S}
    if not all(config[name] for name in ("key", "team", "url")):
        p.error("Définir KOTH_HILL_KEY, KOTH_TEAM et KOTH_URL dans l'environnement.")
    url = urllib.parse.urlsplit(config["url"])
    if url.scheme not in ("http", "https") or not url.hostname or url.username or url.password:
        p.error("KOTH_URL doit être une URL HTTP(S) valide sans identifiants intégrés.")
    print(f"EXÉCUTION bornée vers {url.hostname} : {args.claims} tentative(s) maximum.")
    trial(args, config)


if __name__ == "__main__":
    mp.freeze_support()
    try:
        main()
    except KeyboardInterrupt:
        print("Arrêt manuel : aucune nouvelle tentative.")
