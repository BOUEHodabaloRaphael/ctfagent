---
doc_kind: pattern
title: "Race condition TOCTOU sur logique de paiement/solde"
category: web
slug: edoulooo-race-condition
created: 2026-10-29
status: active
tags:
  - web
  - race-condition
  - toctou
  - business-logic
  - concurrency
chain_summary: "Check de solde puis debit non atomiques = exploitable par rafale de requetes concurrentes faisant passer le solde en negatif."
---
# Race condition TOCTOU sur logique de paiement/solde

## Chain Summary

- One-line chain: Check de solde puis debit non atomiques = exploitable par rafale de requetes concurrentes faisant passer le solde en negatif.
- Typical target shape: Logique metier avec verification d'une condition (solde, stock, quota) suivie d'une action (debit, decrement) sans transaction atomique/verrou.

## Preconditions

- Logique metier avec verification d'une condition (solde, stock, quota) suivie d'une action (debit, decrement) sans transaction atomique/verrou.

## Cheap Probes

- Tester l'action une seule fois pres de la limite (succes/echec normal), puis la meme action en rafale concurrente (pas en sequentiel navigateur).

## Telltale Evidence

- Le solde/stock final devient negatif ou incoherent, ou plusieurs actions qui devraient etre mutuellement exclusives reussissent toutes.

## Escalation Order

1. Identifier une action avec check-puis-action sur un etat partage (solde, stock, usage unique).
2. Verifier d'abord le comportement normal en sequentiel.
3. Envoyer N requetes identiques en vraie concurrence via un client natif (ThreadPoolExecutor/Python, Burp Turbo Intruder, ou multipart single-packet si HTTP/2).
4. Observer si l'etat final viole l'invariant attendu (solde negatif, double redemption, etc.).

## Common Mistakes

- Tester la concurrence avec des requetes de navigateur limitees en connexions paralleles par hote (souvent 6) au lieu d'un client natif sans cette limite.

## Payload Shapes

```text
ThreadPoolExecutor(max_workers=50).map(lambda _: requests.post(url, data=...), range(50))
```

## Related Writeups

- edoulooo-race-condition

## Skill Impact

- Related skill: web-triage: ajouter race-condition/TOCTOU comme sous-categorie de business-logic avec le rappel client-natif-vs-navigateur.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
