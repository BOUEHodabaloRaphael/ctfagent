---
doc_kind: pattern
title: "LWE avec secret restreint (binaire) bruteforcable"
category: crypto
slug: adokpo-lwe-esig
created: 2026-10-29
status: active
tags:
  - crypto
  - lwe
  - lattice
  - brute-force
  - python
chain_summary: "Instance LWE avec espace secret restreint (ex: binaire): bruteforce + scoring sur la somme des erreurs centrees au carre plutot que LLL/BKZ."
---
# LWE avec secret restreint (binaire) bruteforcable

## Chain Summary

- One-line chain: Instance LWE avec espace secret restreint (ex: binaire): bruteforce + scoring sur la somme des erreurs centrees au carre plutot que LLL/BKZ.
- Typical target shape: Challenge LWE/lattice ou l'enonce ou les params indiquent un secret de forme restreinte (binaire, petites valeurs, sparse).

## Preconditions

- Challenge LWE/lattice ou l'enonce ou les params indiquent un secret de forme restreinte (binaire, petites valeurs, sparse).

## Cheap Probes

- Lire les params fournis (n, q, m) et chercher toute mention de contrainte sur le secret (binaire, ternaire, sparse).

## Telltale Evidence

- Score (somme des erreurs au carre) du bon candidat plusieurs ordres de grandeur sous celui du candidat suivant.

## Escalation Order

1. Verifier la taille de l'espace du secret restreint (2^n pour binaire).
2. Si l'espace est petit (<2^32 raisonnable), bruteforcer directement avec un score d'erreur LWE.
3. Sinon, passer a une vraie reduction de reseau (LLL/BKZ, embedding).

## Common Mistakes

- Se jeter sur LLL/BKZ sans avoir verifie si un simple bruteforce suffit deja.

## Payload Shapes

```text
for s in range(2**n): score = sum(centered(b_i - dot(a_i,s), q)**2 for i in samples)
```

## Related Writeups

- adokpo-lwe-esig

## Skill Impact

- Related skill: web-triage n/a; pertinent pour un futur crypto-triage si cree
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
