---
doc_kind: writeup
title: "Garde de capacite payante fail-open apres logout"
category: web
slug: forge-rodi-gate-fail-open-after-logout
created: 2026-10-29
status: solved
tags:
  - broken-access-control
  - fail-open
  - session-not-revoked
  - business-logic
source: "Programme de divulgation reelle Forge/RodiumAI"
target: "Plateforme Forge (RodiumAI) - API multi-tenant"
---
# Garde de capacite payante fail-open apres logout

## Challenge Summary

- Source: Programme de divulgation reelle Forge/RodiumAI
- Target: Plateforme Forge (RodiumAI) - API multi-tenant
- Goal: Le garde de capacite payante traite un cache de solde absent comme rien a verifier; logout vide ce cache sans revoquer le token, rendant toutes les routes payantes gratuites pour le meme token apres logout.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source report)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Login avec un compte au wallet cache a 0.
2. Appeler logout avec ce meme token -> wallet remis a l'etat absent, mais le token reste valide partout (jamais revoque).
3. Appeler une route gated avec le meme token -> wallet absent -> retour immediat sans exception -> capacite accordee gratuitement.
4. Confirmer via un autre endpoint que le token n'est jamais revoque apres logout.

## Key Evidence

- PoC: wallet "{balanceRodi:0}" avant logout, etat absent apres logout, puis appel direct du garde qui ne leve AUCUNE exception malgre le solde initial insuffisant.

## Dead Ends

- n/a.

## Payloads And Commands

```text
Sequence HTTP login -> logout (meme token) -> appel d'un endpoint payant avec ce token.
```

## Flag / Outcome

- Vulnerabilite confirmee et reportee.

## Reusable Lessons

- Un garde confondant etat 'jamais verifie' et 'verifie et vide': tout controle retournant silencieusement sur un cache absent au lieu de forcer une revalidation live est contournable en declenchant l'invalidation du cache via un endpoint non lie. Meme cause racine que forge-security-review-rodi-gate-bypass (enforcement par endpoint/etat plutot qu'au point d'entree unique).

## Pattern Candidates

- Nouveau pattern: cache-absent-treated-as-pass-fail-open
