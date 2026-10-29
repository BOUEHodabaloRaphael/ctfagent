---
doc_kind: writeup
title: "Holmes CTF 2026 Sherlock 07 - Iron Feather / Mission Vault (drone PX4, dechiffrement ULog)"
category: forensics
slug: ironfeather-sherlock07-px4-ulog-decryption
created: 2026-10-29
status: draft
tags:
  - dfir
  - px4
  - ulog
  - drone-forensics
  - firmware-decryption
  - holmes-ctf
source: "Holmes CTF 2026 - Sherlock 7 Iron Feather (Mission Vault)"
target: "Drone PX4, stockage dataman + journal ULog chiffres"
---
# Holmes CTF 2026 Sherlock 07 - Iron Feather / Mission Vault (drone PX4, dechiffrement ULog)

## Challenge Summary

- Source: Holmes CTF 2026 - Sherlock 7 Iron Feather (Mission Vault)
- Target: Drone PX4, stockage dataman + journal ULog chiffres
- Goal: Drone PX4 recupere avec stockage dataman et journal de vol (.ulg) chiffres; le binaire PX4/px4-dataman stripped fourni comme reference pour reverser le format/mecanisme de chiffrement.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Reverser le binaire px4-dataman (ELF stripped) pour comprendre le format et le schema de chiffrement cible.
2. Dechiffrer le journal de vol chiffre -> succes confirme par le magic bytes 'ULog' + header valide.
3. Dechiffrer le fichier dataman chiffre -> fichier obtenu mais entierement a zero sur l'echantillon inspecte (dechiffrement incertain).
4. Etape suivante attendue: parser le ULog dechiffre (topics vehicle_gps_position/vehicle_status) pour reconstruire les phases de vol.

## Key Evidence

- PARTIELLEMENT CONFIRME: hexdump du journal de vol dechiffre commence par le magic "ULog" suivi d'un header version et de champs lisibles (format valide confirme). NON RESOLU pour le fichier dataman (uniquement des zeros observes, cle/algorithme incertain pour ce second blob).

## Dead Ends

- PARTIELLEMENT RESOLU: le journal de vol est dechiffre avec succes (preuve litterale: magic bytes ULog valide), mais le fichier dataman reste non confirme et aucun flag final n'est etabli. Statut formel: draft.

## Payloads And Commands

```text
Reverse engineering binaire ELF stripped + script de dechiffrement applique a 2 blobs chiffres.
```

## Flag / Outcome

- PARTIELLEMENT RESOLU: le journal de vol est dechiffre avec succes (preuve litterale: magic bytes ULog valide), mais le fichier dataman reste non confirme et aucun flag final n'est etabli. Statut formel: draft.

## Reusable Lessons

- Pour tout stockage proprietaire chiffre d'un firmware embarque, reverser le binaire de reference (meme stripped) pour localiser la routine crypto/cle, valider le succes du dechiffrement via le magic bytes attendu du format clair.

## Pattern Candidates

- Voir pattern associe de meme slug.
