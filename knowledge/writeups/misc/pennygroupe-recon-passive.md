---
doc_kind: writeup
title: "Audit de surface passive - pentest reel (Laravel/OpenResty)"
category: misc
slug: pennygroupe-recon-passive
created: 2026-10-29
status: reference
tags:
  - web
  - recon-passive
  - security-headers
  - server-status
  - spf-dkim-dmarc
  - pentest-reel
source: "Pentest reel (phase 1, reconnaissance passive)"
target: "Application Laravel/PHP derriere OpenResty+Apache (anonymise)"
---
# Audit de surface passive - pentest reel (Laravel/OpenResty)

## Challenge Summary

- Source: Pentest reel (phase 1, reconnaissance passive)
- Target: Application Laravel/PHP derriere OpenResty+Apache (anonymise)
- Goal: Phase de reconnaissance passive (non intrusive) revelant absence totale d'en-tetes de securite HTTP, divulgation de pile technique, et endpoint /server-status accessible (403 au lieu de 404).

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Fingerprint infra: OpenResty + Apache 2.4.62 (Debian) + PHP 8.3.21 + Laravel (cookies/CSRF).
2. curl -I: aucun des 6 en-tetes de securite recommandes (HSTS, X-Frame-Options, CSP, X-Content-Type-Options, Referrer-Policy, Permissions-Policy).
3. /server-status repond 403 (pas 404) -> mod_status charge, module masque pas supprime, version Apache divulguee dans la page d'erreur.
4. DNS: SPF softfail (~all), DKIM absent, DMARC quarantine peu efficace sans DKIM -> risque de spoofing.
5. 5 mesures TTFB repetees: variations importantes avec timeouts transitoires sur certaines routes.
6. Fichiers sensibles standards (.env, .git, telescope, ignition) correctement en 404 - bonnes pratiques confirmees sur ce volet.

## Key Evidence

- curl -sSI confirmant l'absence des 6 en-tetes; /server-status en 403 avec corps revelant la version Apache; enregistrement SPF "~all" et absence de default._domainkey; mesures TTFB variables.

## Dead Ends

- Fichiers sensibles standards (.env, .git) correctement proteges - piste fermee, bonne pratique du client.

## Payloads And Commands

```text
Requetes HTTP/DNS passives uniquement (curl -I, openssl s_client, dig) - aucun test actif, phase 1 autorisee uniquement.
```

## Flag / Outcome

- n/a - rapport de recon, pas de flag.

## Reusable Lessons

- Checklist recon passive pre-intrusive utile avant toute phase active necessitant autorisation ecrite.

## Pattern Candidates

- Nouveau pattern: passive-recon-checklist
