---
doc_kind: writeup
title: "OAuth login CSRF / session fixation - binding PKCE state optionnel"
category: web
slug: forge-oauth-login-csrf-state-binding-optional
created: 2026-10-29
status: solved
tags:
  - oauth
  - csrf
  - login-csrf
  - pkce-state
  - opt-in-security-control
source: "Programme de divulgation reelle Forge/RodiumAI"
target: "Plateforme Forge (RodiumAI) - API multi-tenant"
---
# OAuth login CSRF / session fixation - binding PKCE state optionnel

## Challenge Summary

- Source: Programme de divulgation reelle Forge/RodiumAI
- Target: Plateforme Forge (RodiumAI) - API multi-tenant
- Goal: Le binding du state OAuth a la session navigateur n'est applique que si un parametre optionnel est fourni a l'initiation; en l'omettant, un attaquant fait authentifier une victime sous son propre compte.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source report)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Attaquant appelle le start OAuth SANS le parametre de binding -> state sans claim de liaison.
2. Attaquant complete le flux avec son propre compte, capture code+state.
3. Attaquant envoie a la victime un lien de callback avec ce code+state.
4. Le state n'ayant pas de claim de liaison, le check est skippe -> callback accepte -> victime authentifiee en tant qu'attaquant.

## Key Evidence

- PoC bout-en-bout: victime authentifiee comme attaquant; table comparative des 4 combinaisons bound/unbound x binding present/absent.

## Dead Ends

- n/a.

## Payloads And Commands

```text
Lien de callback OAuth (code+state captures) envoye a la victime.
```

## Flag / Outcome

- Vulnerabilite confirmee et reportee.

## Reusable Lessons

- Une protection anti-CSRF OAuth opt-in au lieu d'obligatoire: si l'enforcement d'un binding de state depend d'un parametre optionnel, l'attaquant choisit simplement de ne pas l'activer.

## Pattern Candidates

- Nouveau pattern: oauth-state-binding-opt-in-bypass
