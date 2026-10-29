---
doc_kind: writeup
title: FAFA
category: misc
slug: fafa-whitespace-stego
created: 2026-10-29
status: solved
tags:
  - misc
  - steganography
  - whitespace-stego
  - base64
  - zip-cracking
source: "ESIG TECH ARENA CTF 2026"
target: "Fichier texte anodin + ZIP protege"
---
# FAFA

## Challenge Summary

- Source: ESIG TECH ARENA CTF 2026
- Target: Fichier texte anodin + ZIP protege
- Goal: Chaine de steganographie multi-couches: whitespace-stego (snow) dans un texte anodin, decodant en base64 vers une archive ZIP protegee cassable par dictionnaire.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Fichier texte = faux email anodin, rien de suspect en lecture normale.
2. `cat -A` revele des tabulations/espaces invisibles en fin de ligne (whitespace stego).
3. `stegsnow -C` extrait un blob base64 (signature ZIP PK une fois decode).
4. Decodage base64 -> ZIP valide, protege ZipCrypto.
5. `fcrackzip -u -D -p rockyou.txt` -> mot de passe trouve quasi instantanement.
6. Extraction de flag.txt.

## Key Evidence

- Tabulations/espaces invisibles reveles par cat -A; blob base64 commençant par signature ZIP PK\x03\x04; mot de passe casse 'stealth123'; flag flag{l@y37s_0n_l@y3rs}.

## Dead Ends

- n/a.

## Payloads And Commands

```text
Extraction stegsnow -C, decodage base64, cassage fcrackzip dictionnaire.
```

## Flag / Outcome

- flag{l@y37s_0n_l@y3rs}

## Reusable Lessons

- Texte anodin avec espaces/tabulations invisibles en fin de ligne = whitespace steganography (snow/stegsnow), tester `cat -A` systematiquement. Chaine texte->stego->base64->zip->mdp est un pattern recurrent de challenges misc multi-couches.

## Pattern Candidates

- Nouveau pattern: whitespace-stego-multilayer-chain
