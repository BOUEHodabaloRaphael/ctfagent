---
doc_kind: writeup
title: Edoulooo
category: web
slug: edoulooo-race-condition
created: 2026-10-29
status: solved
tags:
  - web
  - race-condition
  - toctou
  - business-logic
  - concurrency
source: "ESIG TECH ARENA CTF 2026"
target: "Logique d'achat boutique (check solde + debit)"
---
# Edoulooo

## Challenge Summary

- Source: ESIG TECH ARENA CTF 2026
- Target: Logique d'achat boutique (check solde + debit)
- Goal: Race condition/TOCTOU sur la logique d'achat (verification de solde puis debit non atomiques), exploitable par requetes concurrentes pour passer le solde en negatif.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Pas de session/auth, etat (solde) global partage.
2. Credit via /faucet jusqu'a 400, test /buy a 300 -> succes sans flag (message generique).
3. Hypothese TOCTOU (check solde>=300 puis debit non atomique).
4. Rafale de POST /buy reellement simultanees (Python ThreadPoolExecutor, hors navigateur pour contourner la limite de connexions par hote).
5. Plusieurs requetes lisent le meme solde 'suffisant' avant debit -> solde final negatif -> flag retourne.

## Key Evidence

- Reponse serveur passant a "FELICITATIONS !" + flag dès que le solde devient negatif; flag EthACTF{race_to_flash}.

## Dead Ends

- Test unitaire /buy a 300 sans concurrence ne declenchait rien (etape necessaire mais pas suffisante).

## Payloads And Commands

```text
Rafale de POST /buy concurrentes via ThreadPoolExecutor (client natif, pas navigateur).
```

## Flag / Outcome

- EthACTF{race_to_flash}

## Reusable Lessons

- Race condition/TOCTOU sur logique de paiement (check puis debit non atomiques) exploitable par requetes paralleles massives. Utiliser un client HTTP natif pour depasser la limite de connexions concurrentes du navigateur.

## Pattern Candidates

- Nouveau pattern: toctou-payment-race-condition
