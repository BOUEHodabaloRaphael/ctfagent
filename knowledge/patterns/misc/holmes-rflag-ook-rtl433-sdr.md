---
doc_kind: pattern
title: "Holmes CTF rflag (Hardware) - capture SDR OOK decodee automatiquement avec rtl_433"
category: misc
slug: holmes-rflag-ook-rtl433-sdr
created: 2026-10-29
status: active
tags:
  - sdr
  - rtl-433
  - ook-modulation
  - iq-capture
  - hardware-ctf
  - hex-to-ascii
chain_summary: "Capture IQ d'un signal 433 MHz identifiee comme modulation OOK par analyse FFT/enveloppe, decodee automatiquement par rtl_433 pour extraire un payload hex converti en ASCII contenant le flag."
---
# Holmes CTF rflag (Hardware) - capture SDR OOK decodee automatiquement avec rtl_433

## Chain Summary

- One-line chain: Capture IQ d'un signal 433 MHz identifiee comme modulation OOK par analyse FFT/enveloppe, decodee automatiquement par rtl_433 pour extraire un payload hex converti en ASCII contenant le flag.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- rtl_433 -A sort une trame hex qui, convertie en ASCII apres retrait du preambule, donne directement le flag.

## Escalation Order

1. Extraction de l'archive -> fichier IQ complex float32.
2. Analyse FFT: porteuse decalee, deux niveaux d'enveloppe nets -> modulation OOK/ASK.
3. Mesure des durees de run -> protocole type sonde 433 MHz avec preambule.
4. Decodage automatique rtl_433 -A -> trame hex brute.
5. Retrait du preambule/octets de trame, conversion hex -> ASCII -> flag.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste.

## Payload Shapes

```text
Pour tout challenge hardware/SDR fournissant un .cf32/.cu8, toujours tester rtl_433 -A en premier (detection automatique de dizaines de protocoles OOK/FSK) avant d'ecrire un demodulateur FFT manuel.
```

## Related Writeups

- holmes-rflag-ook-rtl433-sdr

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
