---
doc_kind: writeup
title: "Paid-capability gate bypass sur POST /projects/{id}/security-review"
category: web
slug: forge-security-review-rodi-gate-bypass
created: 2026-10-29
status: solved
tags:
  - broken-access-control
  - business-logic
  - missing-authorization-check
  - rodi-wallet
source: "Programme de divulgation reelle Forge/RodiumAI"
target: "Plateforme Forge (RodiumAI) - API multi-tenant"
---
# Paid-capability gate bypass sur POST /projects/{id}/security-review

## Challenge Summary

- Source: Programme de divulgation reelle Forge/RodiumAI
- Target: Plateforme Forge (RodiumAI) - API multi-tenant
- Goal: L'endpoint security-review execute un appel IA payant complet sans jamais appeler le garde de capacite payante, permettant une generation facturable gratuite a solde nul.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source report)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Constater que tous les endpoints IA (chat/SEO/design) appellent le garde sauf security_review_project().
2. Creer un compte avec solde RODI = 0.
3. Appeler un endpoint gate -> 402 INSUFFICIENT_RODI.
4. Appeler security-review avec le meme solde -> erreur differente (jamais 402) -> garde jamais consulte.
5. Confirmer l'execution de l'appel IA billable malgre le solde insuffisant.

## Key Evidence

- PoC: endpoint gate renvoie 402, endpoint non gate renvoie une erreur differente jamais 402, pour le meme wallet a 0 RODI.

## Dead Ends

- n/a.

## Payloads And Commands

```text
Script Python PoC HTTP (register, seed wallet, appels comparatifs).
```

## Flag / Outcome

- Vulnerabilite confirmee et reportee.

## Reusable Lessons

- Garde de capacite payante applique par endpoint plutot qu'au point d'entree partage: chaque nouvelle route IA doit etre auditee individuellement.

## Pattern Candidates

- Lie au pattern forge-rodi-gate-fail-open-after-logout (meme cause racine: enforcement par endpoint/etat plutot qu'au point d'entree unique).
