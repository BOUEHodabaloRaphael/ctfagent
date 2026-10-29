---
doc_kind: writeup
title: "ADOKPO (LWE toy instance)"
category: crypto
slug: adokpo-lwe-esig
created: 2026-10-29
status: solved
tags:
  - crypto
  - lwe
  - lattice
  - brute-force
  - python
source: "ESIG TECH ARENA CTF 2026"
target: "LWE params.json/samples.json (n=8, q=127)"
---
# ADOKPO (LWE toy instance)

## Challenge Summary

- Source: ESIG TECH ARENA CTF 2026
- Target: LWE params.json/samples.json (n=8, q=127)
- Goal: Instance LWE jouet avec secret explicitement binaire, brute-forcable au lieu de LLL/BKZ.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Lire params.json/samples.json: n=8, q=127, m=24, secret note explicitement binaire.
2. Constat: secret binaire = 2^8=256 candidats, bruteforce direct legitime plutot que reduction de reseau.
3. Pour chaque candidat s, calculer l'erreur centree e_i = centered(b_i - <a_i,s> mod q) sur 24 echantillons.
4. Score = somme des carres des erreurs, minimal pour le bon secret.
5. s=10111110 (score 16) vs 2e candidat score 16033 (3 ordres de grandeur d'ecart).
6. Verifier independamment les residus (tous dans {-1,0,1}, aucun proche de q/2).

## Key Evidence

- s=10111110 (binaire)=190=0xbe ; score 16 vs 16033 pour le candidat suivant.

## Dead Ends

- Tentative de reduction de reseau LLL/BKZ aurait ete inutilement couteuse ici.

## Payloads And Commands

```text
Script Python pur: bruteforce 256 candidats + calcul de residus LWE.
```

## Flag / Outcome

- Secret binaire recupere, flag derive du secret.

## Reusable Lessons

- Toujours verifier la taille de l'espace du secret (ex: binaire = 2^n) avant de sortir l'artillerie lourde (LLL/BKZ).

## Pattern Candidates

- Nouveau pattern: lwe-binary-secret-bruteforce
