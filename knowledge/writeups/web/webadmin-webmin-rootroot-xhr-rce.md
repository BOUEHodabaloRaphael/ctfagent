---
doc_kind: writeup
title: "ThunderCipher WebAdmin - Webmin root:root et RCE via module Command Shell (piege XHR)"
category: web
slug: webadmin-webmin-rootroot-xhr-rce
created: 2026-10-29
status: solved
tags:
  - webmin-default-creds
  - xhr-header-bypass
  - csrf-protection-trap
  - command-shell-module
source: thundercipher.in/labs
target: "Webmin avec creds par defaut"
---
# ThunderCipher WebAdmin - Webmin root:root et RCE via module Command Shell (piege XHR)

## Challenge Summary

- Source: thundercipher.in/labs
- Target: Webmin avec creds par defaut
- Goal: Identifiants par defaut root:root sur Webmin donnent acces au module Command Shell, mais la requete echoue silencieusement sans le header X-Requested-With: XMLHttpRequest.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Login Webmin root:root.
2. Tentative directe sur shell/index.cgi sans header -> echec silencieux.
3. Ajout header X-Requested-With: XMLHttpRequest + referer correct -> execution acceptee.
4. Commande -> flag recupere directement.

## Key Evidence

- Echec sans header XHR puis succes identique avec header ajoute.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
curl -H 'X-Requested-With: XMLHttpRequest' -F 'cmd=...' vers shell/index.cgi.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Sur Webmin, toujours tester le header X-Requested-With pour tout module qui ne repond rien; si plusieurs modules semblent casses, prioriser le module Command Shell.

## Pattern Candidates

- Voir pattern associe de meme slug.
