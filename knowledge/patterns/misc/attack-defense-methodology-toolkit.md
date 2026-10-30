---
doc_kind: pattern
title: "Methodologie Attack-Defense CTF — mecanique, ordre des operations, toolkit"
category: misc
slug: attack-defense-methodology-toolkit
created: 2026-10-30
status: active
tags:
  - koth
  - attack-defense
  - nctf26
  - methodology
  - competition-prep
chain_summary: "Reverse d'abord (15-20 min, pas de patch precipite), des qu'un exploit marche en solo -> le lancer en boucle sur toutes les equipes AVANT de patcher, patcher seulement apres, surveiller son propre SLA en continu."
---
# Methodologie Attack-Defense CTF — mecanique, ordre des operations, toolkit

## Chain Summary

- One-line chain: Reverse d'abord (15-20 min, pas de patch precipite), des qu'un exploit marche en solo -> le lancer en boucle sur toutes les equipes AVANT de patcher, patcher seulement apres, surveiller son propre SLA en continu.

## Preconditions

- Format Attack-Defense (ICC/ENISA, HackTheBox A/D, Kaspersky SAS-style, ou la finale NCTF26 'sur site, offensif et defensif' a Lome): toutes les equipes ont la meme topologie de services vulnerables. Boucle de jeu = un tick (SLA checker, souvent 90-120s) qui publie de nouveaux flag IDs par service — le flag change a chaque tick, l'ID qui y mene est publie en clair par le gameserver. Score = + flags voles soumis, - flags perdus, +/- disponibilite SLA de son propre service.

## Cheap Probes

- Des le debut du match: identifier la topologie de services fournie (meme binaire/code source pour toutes les equipes), reperer le mecanisme de flag ID publie par le gameserver.

## Telltale Evidence

- Toolkit deja construit et pret: src/tools/ctf/attack_defense_toolkit/ (exploit_runner.py, submitter.py, sla_monitor.py, pcap_watch.py, exploits/template.py+web_classic.py+llm_prompt_injection.py). Prep initiale faite pour AFRICC/ICC (2026-09-14).

## Escalation Order

1. Premieres ~15-20 min: reverser le(s) service(s) fourni(s), PAS de patch precipite (patcher trop vite/mal = service down = perte de points SLA garantie).
2. Des qu'un exploit marche en solo (teste via `exploit_runner.py exploits/<service>.py --once --targets 127.0.0.1` ou une instance de test), le lancer en boucle sur TOUTES les equipes le plus tot possible, AVANT que les autres patchent (`exploit_runner.py exploits/<service>.py` sans --once).
3. Patcher SEULEMENT apres avoir un exploit qui marche deja en boucle — patcher en premier = perdre le volet attaque pendant la defense.
4. Lancer sla_monitor.py en continu sur ses propres services: un patch mal teste qui casse le service coute souvent plus cher que ne pas patcher du tout.
5. Lancer pcap_watch.py sur ses propres ports pour copier/comprendre les payloads adverses — souvent le patch le plus rapide est un blocage regex cible plutot qu'un vrai fix de code.
6. Remplir config.py (IP equipes, FLAG_REGEX, endpoint de soumission, duree du tick, propres services) avant le debut du match; l'endpoint reel de arena.ctf.tg pour la finale sera annonce sur place.

## Common Mistakes

- Ne jamais couper sla_monitor.py — c'est le seul signal fiable que le patch n'a pas casse le service. Ne jamais patcher avant d'avoir un exploit fonctionnel pret a tourner en boucle (perte du volet offensif).

## Payload Shapes

```text
python3 exploit_runner.py exploits/<service>.py --once --targets 127.0.0.1   # test solo d'abord
python3 exploit_runner.py exploits/<service>.py                     # boucle sur toutes les equipes
```

## Related Writeups

- src/tools/ctf/attack_defense_toolkit/README.md (workflow complet, 1 pane tmux par outil)

## Skill Impact

- Related skill: ctf-solver-profile: ajouter le format Attack-Defense comme mode de jeu distinct avec son propre ordre d'operations (reverse->exploit-boucle->patch), pertinent pour la finale NCTF26 a Lome (19-20 nov, 'sur site, offensif et defensif').
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
