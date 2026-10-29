---
doc_kind: writeup
title: "Holmes CTF 2026 Sherlock 06 - Silent Passenger (firmware IVI/Carplay vehicule)"
category: forensics
slug: silentpassenger-sherlock06-ivi-firmware-extraction
created: 2026-10-29
status: draft
tags:
  - dfir
  - firmware
  - ivi-carplay
  - ext4-mount
  - automotive-forensics
  - holmes-ctf
source: "Holmes CTF 2026 - Sherlock 6 Silent Passenger"
target: "Image firmware infotainment embarque"
---
# Holmes CTF 2026 Sherlock 06 - Silent Passenger (firmware IVI/Carplay vehicule)

## Challenge Summary

- Source: Holmes CTF 2026 - Sherlock 6 Silent Passenger
- Target: Image firmware infotainment embarque
- Goal: La narration pointe vers l'unite centrale (head unit) d'un vehicule dont le logiciel aurait servi un second usage cache; artefact fourni est une image firmware d'infotainment deja extraite en partitions ext4/data.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Extraire l'archive firmware -> plusieurs partitions (dont un system.img ext4 valide).
2. Monter system.img en lecture pour explorer l'arborescence de l'IVI.
3. Lire le changelog de build (contexte Carplay/Google Store, pas de contenu forensics direct).
4. Etape suivante attendue (non realisee): chercher dans system.img les logs Bluetooth/pairing, historique navigation, logs reseau caches.

## Key Evidence

- NON RESOLU: `file system.img` confirme un ext4 valide et montable; aucun resultat d'analyse texte (logs Bluetooth/GPS trouves) n'est present localement.

## Dead Ends

- NON RESOLU. Partition system.img montee avec succes (etape technique confirmee), mais aucune reponse finale n'est etablie. Statut formel: draft.

## Payloads And Commands

```text
Extraction archive + montage loop ext4 d'une image firmware embarquee automobile.
```

## Flag / Outcome

- NON RESOLU. Partition system.img montee avec succes (etape technique confirmee), mais aucune reponse finale n'est etablie. Statut formel: draft.

## Reusable Lessons

- Triage firmware IVI: extraire l'archive -> identifier les partitions via `file` -> monter l'ext4 en lecture -> chercher logs Bluetooth/GPS/reseau caches comme second canal de telemetrie.

## Pattern Candidates

- Voir pattern associe de meme slug.
