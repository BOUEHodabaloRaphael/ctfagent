---
doc_kind: writeup
title: "FullHouse - L'indice (exploit portefeuille blockchain, montant negatif)"
category: web
slug: fullhouse-blockchain-negative-amount
created: 2026-10-29
status: solved
tags:
  - blockchain
  - business-logic
  - signature-cote-client
  - base64-creds
  - casino
source: "HTB Pro Lab FullHouse"
target: "Application casino avec transactions blockchain signees client"
---
# FullHouse - L'indice (exploit portefeuille blockchain, montant negatif)

## Challenge Summary

- Source: HTB Pro Lab FullHouse
- Target: Application casino avec transactions blockchain signees client
- Goal: L'application casino fait confiance a des transactions blockchain signees cote client; une transaction forgee avec un montant negatif credite le compte, debloquant une zone VIP dont une requete intercept fuite un mot de passe base64.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. nmap standard -> ssh et http (nginx, casino).
2. Inscription expose une paire de cles RSA et une adresse publique.
3. Script Python forge une transaction avec montant negatif, signee cote client -> credite le compte.
4. Acces zone VIP debloque; interception de la requete d'action -> header Authorization en base64.
5. Decodage base64 -> credentials -> SSH -> flag.

## Key Evidence

- le decodage base64 du header renvoie directement des credentials en clair.

## Dead Ends

- n/a (see Reusable Lessons for pitfalls encountered)

## Payloads And Commands

```text
transaction JSON/blockchain signee avec montant negatif forge cote client.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Toute logique financiere/blockchain qui fait confiance a une signature cote client sans validation serveur du montant permet de forger des valeurs negatives pour crediter un compte; toujours intercepter les headers Authorization sur les endpoints premium, souvent du Basic auth encode en base64.

## Pattern Candidates

- Nouveau pattern: fullhouse-blockchain-negative-amount
