---
doc_kind: writeup
title: "Deni de service plateforme via regex quadratique dans la detection d'embeds"
category: web
slug: forge-redos-embed-detection-dos
created: 2026-10-29
status: solved
tags:
  - redos
  - dos
  - regex-backtracking
  - event-loop-blocking
  - single-worker
source: "Programme de divulgation reelle Forge/RodiumAI"
target: "Plateforme Forge (RodiumAI) - API multi-tenant"
---
# Deni de service plateforme via regex quadratique dans la detection d'embeds

## Challenge Summary

- Source: Programme de divulgation reelle Forge/RodiumAI
- Target: Plateforme Forge (RodiumAI) - API multi-tenant
- Goal: Un regex de detection d'embeds tiers a un comportement de backtracking quadratique; un message de chat adversarial de 50k caracteres bloque l'event-loop unique du serveur plusieurs secondes pour tous les utilisateurs.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source report)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Le regex de detection d'embeds s'execute synchroneement sur chaque message de chat, sans offload thread.
2. Mesure offline: temps de traitement croissant de maniere quadratique avec la taille de l'entree.
3. Payload repetant un motif cible jusqu'a la limite de taille de message (50k caracteres).
4. Envoi via un compte normal, sans privilege particulier.
5. Mesure parallele d'une requete non liee (autre compte): latence normale pendant le traitement du payload, reproduit 2x.

## Key Evidence

- Table de timing offline croissance quadratique; mesure live: requete d'un autre utilisateur passant de quelques ms a plusieurs secondes pendant le traitement du payload malveillant.

## Dead Ends

- n/a. Finding secondaire note dans le meme audit: endpoint OAuth callback sans rate limit et state replayable.

## Payloads And Commands

```text
Chaine de 50000 caracteres repetant un motif declencheur comme contenu de message de chat JSON.
```

## Flag / Outcome

- Vulnerabilite confirmee et reportee.

## Reusable Lessons

- ReDoS sur event-loop unique mono-worker: regex a quantificateurs non bornes executee synchroneement dans un handler async sans thread-offload sur une app a un seul worker transforme un DoS local en DoS plateforme entiere.

## Pattern Candidates

- Nouveau pattern: redos-single-worker-platform-wide-dos
