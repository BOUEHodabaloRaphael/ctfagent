---
doc_kind: writeup
title: Broken
category: crypto
slug: broken-padding-oracle
created: 2026-10-29
status: solved
tags:
  - crypto
  - padding-oracle
  - aes-cbc
  - pkcs7
  - cbc-byte-at-a-time
source: "ESIG TECH ARENA CTF 2026"
target: "Oracle de padding PKCS7 (AES-CBC) via endpoint HTTP"
---
# Broken

## Challenge Summary

- Source: ESIG TECH ARENA CTF 2026
- Target: Oracle de padding PKCS7 (AES-CBC) via endpoint HTTP
- Goal: Oracle de padding PKCS7 local (AES-CBC) expose via GET, exploite par l'attaque byte-at-a-time CBC padding-oracle standard pour dechiffrer sans connaitre la cle.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Dezippage oracle.py (serveur HTTP local), ciphertext.txt.
2. GET /?ct=<hex> renvoie VALID/BAD_PADDING/BAD_FORMAT selon la validite du padding PKCS7.
3. Recuperation du ciphertext reel (2 blocs de 16 octets).
4. Attaque byte-at-a-time CBC padding-oracle par bloc, revelant l'etat intermediaire D_K(bloc), XOR avec le bloc precedent pour obtenir le clair.
5. Resultat: flag apres retrait du padding.

## Key Evidence

- Reponses VALID/BAD_PADDING de l'oracle; flag obtenu sans lire la cle en clair presente dans le script fourni (attaque menee en aveugle pour rester generalisable).

## Dead Ends

- n/a - lire directement la cle dans le script aurait ete possible mais moins generalisable; l'attaque en aveugle a ete privilegiee.

## Payloads And Commands

```text
Requetes GET /?ct=<hex> avec blocs manipules octet par octet (CBC padding-oracle).
```

## Flag / Outcome

- EthACTF{padding_is_information}

## Reusable Lessons

- Endpoint exposant un oracle de padding PKCS7 (reponse differenciee VALID/BAD_PADDING) = dechiffrement complet sans cle via byte-at-a-time CBC padding-oracle.

## Pattern Candidates

- Nouveau pattern: cbc-padding-oracle-byte-at-a-time
