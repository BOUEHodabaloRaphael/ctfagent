---
doc_kind: writeup
title: "DANTE NIX04 - SQLi error-based MariaDB puis bypass sudo -u#-1"
category: web
slug: nix04-sqli-errorbased-sudo-uid-bypass
created: 2026-10-29
status: solved
tags:
  - sqli-error-based
  - sqlmap
  - extractvalue
  - sudo-uid-bypass
  - mariadb
source: "HTB Pro Lab DANTE"
target: "MariaDB + regle sudo NOPASSWD mal restreinte"
---
# DANTE NIX04 - SQLi error-based MariaDB puis bypass sudo -u#-1

## Challenge Summary

- Source: HTB Pro Lab DANTE
- Target: MariaDB + regle sudo NOPASSWD mal restreinte
- Goal: Injection SQL error-based (EXTRACTVALUE) sur un parametre pour dump rapide; creds applicatifs donnent un acces avec sudo NOPASSWD /bin/bash, contourne via sudo -u#-1 (UID -1 = 4294967295 = root).

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Parametre GET -> erreur SQL MariaDB confirmant l'injection.
2. sqlmap --technique=BEUSTQ --dbs confirme injectable.
3. sqlmap --technique=E --string=<marqueur> pour dump direct via EXTRACTVALUE -> flag.
4. Creds applicatifs trouves en base.
5. sudo -l -> (ALL) NOPASSWD: /bin/bash.
6. sudo -u#-1 root (UID -1 interprete comme root) -> shell root.

## Key Evidence

- Message d'erreur MariaDB confirmant l'injection; sortie sqlmap confirmant error-based (EXTRACTVALUE) injectable.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
sqlmap --technique=E --string=<marqueur>; sudo -u#-1 root.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Error-based EXTRACTVALUE permet un dump direct sans --dbs/--dump (gain de temps); sudo -u#<valeur negative> est une technique de bypass UID classique quand NOPASSWD est mal restreint.

## Pattern Candidates

- Voir pattern associe de meme slug.
