---
doc_kind: writeup
title: "Open redirect - sanitizeReturnTo contourne via backslash"
category: web
slug: forge-open-redirect-backslash-bypass
created: 2026-10-29
status: solved
tags:
  - open-redirect
  - url-parsing
  - backslash-normalization
  - oauth-phishing
source: "Programme de divulgation reelle Forge/RodiumAI"
target: "Plateforme Forge (RodiumAI) - API multi-tenant"
---
# Open redirect - sanitizeReturnTo contourne via backslash

## Challenge Summary

- Source: Programme de divulgation reelle Forge/RodiumAI
- Target: Plateforme Forge (RodiumAI) - API multi-tenant
- Goal: Le sanitizer bloque les URLs commencant par // mais pas /\\, que les navigateurs normalisent en //, permettant une redirection post-authentification vers un domaine externe.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source report)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. sanitizeReturnTo() teste startsWith('/') && !startsWith('//').
2. Construire next=/\\evil.com - commence par / pas //, accepte tel quel.
3. Le navigateur normalise le backslash en slash a la navigation -> //evil.com.
4. Variante absolue avec userinfo/backslash passe le test d'origine mais son pathname se normalise aussi en //evil.com.
5. Verifie sur 4 sinks (login, register, callback OAuth, popup OAuth).

## Key Evidence

- Reproduction deterministe avec le meme parseur URL que le navigateur: "/\\evil.com" => "https://evil.com/"; tests unitaires existants ne couvrant jamais la variante backslash.

## Dead Ends

- n/a.

## Payloads And Commands

```text
Parametre next=/\\evil.com ou /%5Cevil.com dans une URL de login/register/callback.
```

## Flag / Outcome

- Vulnerabilite confirmee et reportee.

## Reusable Lessons

- Une validation par prefixe de chaine brute au lieu de parser l'URL: tout sanitizer testant startsWith sur l'entree brute avant resolution est contournable via normalisation navigateur (backslash, encodage, userinfo @).

## Pattern Candidates

- Nouveau pattern: string-prefix-url-sanitizer-bypass
