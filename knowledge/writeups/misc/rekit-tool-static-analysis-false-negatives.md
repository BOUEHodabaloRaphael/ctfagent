---
doc_kind: writeup
title: "Retour de test REKitV2.py - faux negatifs checksec et fausses alertes crypto"
category: misc
slug: rekit-tool-static-analysis-false-negatives
created: 2026-10-29
status: solved
tags:
  - checksec
  - false-negative
  - readelf-sw
  - stripped-binary
  - tool-validation
  - static-analysis
source: "Test d'outil interne (REKITV2.py v2.1)"
target: "Outil de triage reverse-engineering maison"
---
# Retour de test REKitV2.py - faux negatifs checksec et fausses alertes crypto

## Challenge Summary

- Source: Test d'outil interne (REKITV2.py v2.1)
- Target: Outil de triage reverse-engineering maison
- Goal: Sur un lab de verifications compilees avec contenu connu a l'avance, plusieurs echouent: canary non detecte sur binaires strippes faute d'option readelf adaptee, alerte RC4 qui se declenche sur presque tout binaire, Fortify confondu avec un simple canary, entropie par section faussee par un decalage de colonnes.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Comparer la sortie de l'outil a une verite etablie par readelf brut sur des binaires compiles avec contenu connu.
2. readelf -sW (symboles versionnes) montre le canary present sur un binaire stripped, alors que l'outil (readelf -s sans -W) le manque.
3. Alerte RC4 de l'outil declenchee sur un binaire quelconque sans aucun RC4 reel -> faux positif heuristique.
4. Verifier chaque heuristique de l'outil contre un cas de controle avant de lui faire confiance en conditions reelles.

## Key Evidence

- readelf -sW montre le symbole du canary sur le binaire stripped alors que REKit repond Canary: Non; alerte RC4 declenchee sur un binaire sans RC4.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
Suite de tests comparant la sortie de l'outil a une verite etablie par readelf brut sur des binaires de controle.
```

## Flag / Outcome

- Flag obtenu / finding confirme, chaine terminee.

## Reusable Lessons

- Avant de faire confiance au checksec d'un outil de triage maison: verifier qu'il utilise readelf -sW (pas -s) pour resoudre les symboles versionnes sur binaire stripped; verifier que ses heuristiques crypto (motifs d'octets statistiques) ne sont pas de simples faux positifs sans contexte.

## Pattern Candidates

- Voir pattern associe de meme slug.
