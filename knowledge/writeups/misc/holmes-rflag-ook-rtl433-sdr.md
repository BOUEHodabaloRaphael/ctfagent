---
doc_kind: writeup
title: "Holmes CTF rflag (Hardware) - capture SDR OOK decodee automatiquement avec rtl_433"
category: misc
slug: holmes-rflag-ook-rtl433-sdr
created: 2026-10-29
status: solved
tags:
  - sdr
  - rtl-433
  - ook-modulation
  - iq-capture
  - hardware-ctf
  - hex-to-ascii
source: "Holmes CTF 2026"
target: "Capture IQ .cf32, signal 433 MHz"
---
# Holmes CTF rflag (Hardware) - capture SDR OOK decodee automatiquement avec rtl_433

## Challenge Summary

- Source: Holmes CTF 2026
- Target: Capture IQ .cf32, signal 433 MHz
- Goal: Capture IQ d'un signal 433 MHz identifiee comme modulation OOK par analyse FFT/enveloppe, decodee automatiquement par rtl_433 pour extraire un payload hex converti en ASCII contenant le flag.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Extraction de l'archive -> fichier IQ complex float32.
2. Analyse FFT: porteuse decalee, deux niveaux d'enveloppe nets -> modulation OOK/ASK.
3. Mesure des durees de run -> protocole type sonde 433 MHz avec preambule.
4. Decodage automatique rtl_433 -A -> trame hex brute.
5. Retrait du preambule/octets de trame, conversion hex -> ASCII -> flag.

## Key Evidence

- rtl_433 -A sort une trame hex qui, convertie en ASCII apres retrait du preambule, donne directement le flag.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
Outil rtl_433 en mode analyzer (-A) sur fichier IQ; aucun script custom de demodulation necessaire.
```

## Flag / Outcome

- Flag obtenu / finding confirme, chaine terminee.

## Reusable Lessons

- Pour tout challenge hardware/SDR fournissant un .cf32/.cu8, toujours tester rtl_433 -A en premier (detection automatique de dizaines de protocoles OOK/FSK) avant d'ecrire un demodulateur FFT manuel.

## Pattern Candidates

- Voir pattern associe de meme slug.
