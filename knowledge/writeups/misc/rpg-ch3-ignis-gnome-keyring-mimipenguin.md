---
doc_kind: writeup
title: "HTB Endgame RPG — Ch.3 extraction gnome-keyring via mimipenguin"
category: misc
slug: rpg-ch3-ignis-gnome-keyring-mimipenguin
created: 2026-10-29
status: solved
tags:
  - gnome-keyring
  - mimipenguin
  - dbus-unlock
  - linux-post-exploitation
  - credential-dump
source: "HackTheBox Endgame RPG"
target: "Session desktop GNOME active (machine Ignis)"
---
# HTB Endgame RPG — Ch.3 extraction gnome-keyring via mimipenguin

## Challenge Summary

- Source: HackTheBox Endgame RPG
- Target: Session desktop GNOME active (machine Ignis)
- Goal: Depuis le root d'Ignis, recuperation en clair du mot de passe de session desktop via mimipenguin, puis deverrouillage des keyrings GNOME verrouilles pour un appel DBus direct en renommant le keyring cible en login.keyring.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Root sur Ignis observe des process GNOME pour un utilisateur avec session desktop active.
2. mimipenguin.py extrait le mot de passe en clair depuis la memoire.
3. Localisation des fichiers *.keyring et copie non destructive.
4. Collections verrouillees pour un appel DBus direct -> contournement : renommage en login.keyring puis unlock via gnome-keyring-daemon --unlock --components=secrets avec le mot de passe.
5. Lecture des secrets deverrouilles : flag et identifiants divers.

## Key Evidence

- "mimipenguin.py -> [SYSTEM - GNOME] user:password_en_clair"; collection deverrouillee -> flag lu.

## Dead Ends

- Appel DBus direct sur les collections nommees differemment de login.keyring etait refuse - necessitait le renommage pour simuler une session fraiche.

## Payloads And Commands

```text
Renommage de fichier keyring + commande gnome-keyring-daemon --unlock pipee avec le mot de passe.
```

## Flag / Outcome

- Flag obtenu depuis la collection deverrouillee.

## Reusable Lessons

- mimipenguin pour extraire un mot de passe de session GNOME en clair, puis deverrouillage DBus de keyrings verrouilles en renommant le fichier cible en login.keyring pour simuler une session fraiche.

## Pattern Candidates

- Nouveau pattern: gnome-keyring-mimipenguin-dbus-unlock
