---
doc_kind: writeup
title: "SSRF via DNS-rebinding TOCTOU dans la recuperation d'images jointes au chat"
category: web
slug: forge-ssrf-dns-rebinding-toctou-attachments
created: 2026-10-29
status: solved
tags:
  - ssrf
  - dns-rebinding
  - toctou
  - check-then-fetch
source: "Programme de divulgation reelle Forge/RodiumAI"
target: "Plateforme Forge (RodiumAI) - API multi-tenant"
---
# SSRF via DNS-rebinding TOCTOU dans la recuperation d'images jointes au chat

## Challenge Summary

- Source: Programme de divulgation reelle Forge/RodiumAI
- Target: Plateforme Forge (RodiumAI) - API multi-tenant
- Goal: Le garde SSRF valide l'hostname via une premiere resolution DNS, puis une seconde resolution independante est faite par la couche de fetch HTTP; un attaquant controlant son DNS autoritaire renvoie une IP publique au check et une IP interne au connect.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source report)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Pattern resolve-puis-connect: le garde resout/valide le hostname en premier; le client HTTP resout a nouveau le MEME hostname pour se connecter.
2. Attaquant heberge un hostname sous son propre DNS autoritaire, repond IP publique au check et IP interne a la connexion reelle.
3. Message de chat avec marqueur d'attachement image referencant ce hostname.
4. Le garde valide la premiere resolution (publique) -> ALLOWED; le fetch reel se connecte via une seconde resolution independante -> IP interne.
5. PoC: resolveur systeme + service DNS wildcard-vers-IP se connecte reellement en interne via le code de production inchange.

## Key Evidence

- PoC: "[guard check] ... ALLOWED" suivi d'un fetch reussi dont le contenu provient d'un serveur interne local, via le code de production inchange.

## Dead Ends

- n/a.

## Payloads And Commands

```text
Marqueur d'attachement image dans un message de chat referencant une URL sous controle DNS de l'attaquant.
```

## Flag / Outcome

- Vulnerabilite confirmee et reportee.

## Reusable Lessons

- TOCTOU SSRF classique par double resolution DNS independante (check-then-fetch): tout garde qui valide un hostname puis laisse une couche separee le re-resoudre pour se connecter est contournable par DNS rebinding deterministe; seule parade correcte: pinner et reutiliser l'IP deja validee pour la connexion reelle. Meme cause racine que forge-ssrf-window-open-popup-bypass.

## Pattern Candidates

- Nouveau pattern: dns-rebinding-check-then-fetch-ssrf
