---
doc_kind: writeup
title: "Bypass du rate-limit de login via spoofing de X-Forwarded-For"
category: web
slug: forge-xff-ratelimit-bypass-login
created: 2026-10-29
status: solved
tags:
  - rate-limit-bypass
  - x-forwarded-for
  - brute-force
  - auth
source: "Programme de divulgation reelle Forge/RodiumAI"
target: "Plateforme Forge (RodiumAI) - API multi-tenant"
---
# Bypass du rate-limit de login via spoofing de X-Forwarded-For

## Challenge Summary

- Source: Programme de divulgation reelle Forge/RodiumAI
- Target: Plateforme Forge (RodiumAI) - API multi-tenant
- Goal: Le limiteur de debit sur /auth/login cle son compteur sur l'IP extraite du header X-Forwarded-For fourni par le client, sans liste de proxies de confiance; faire varier ce header contourne totalement la defense anti-bruteforce.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source report)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. La fonction d'extraction d'IP client prend le premier segment de X-Forwarded-For tel quel si present, sans verifier la provenance proxy.
2. Baseline: tentatives de login sans header -> blocage apres le seuil configure.
3. Reexecution avec un X-Forwarded-For aleatoire different a chaque requete -> jamais de blocage, toutes traitees normalement.
4. Conclusion: brute-force illimite possible contre tout compte dont l'email est connu, sans autre controle (pas de lockout par compte, pas de captcha).

## Key Evidence

- PoC avec table comparative: baseline bloquee apres le seuil de requetes vs variante avec header spoofe jamais bloquee sur le meme nombre de tentatives.

## Dead Ends

- n/a.

## Payloads And Commands

```text
Requetes HTTP POST /auth/login avec header X-Forwarded-For different (IP aleatoire) a chaque tentative.
```

## Flag / Outcome

- Vulnerabilite confirmee et reportee.

## Reusable Lessons

- Un rate-limiter cle sur un header client non authentifie sans allow-list de proxy de confiance: tout middleware de throttling faisant confiance a X-Forwarded-For sans position fixe dans la chaine de proxy est contournable par rotation du header; necessite un compteur par-compte en complement ou un middleware de proxy avec profondeur de confiance fixee.

## Pattern Candidates

- Nouveau pattern: xff-spoofing-ratelimit-bypass
