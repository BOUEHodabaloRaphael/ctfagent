---
doc_kind: writeup
title: "P.O.O. - BackTrack (chainage de linked servers SQL jusqu'a sa)"
category: web
slug: poo-backtrack-mssql-linked-servers-chain
created: 2026-10-29
status: solved
tags:
  - mssql
  - linked-servers
  - xp_cmdshell
  - privilege-chaining
  - sql-pivot
source: "HTB Mini Pro Lab P.O.O."
target: "Instance MSSQL avec linked servers imbriques"
---
# P.O.O. - BackTrack (chainage de linked servers SQL jusqu'a sa)

## Challenge Summary

- Source: HTB Mini Pro Lab P.O.O.
- Target: Instance MSSQL avec linked servers imbriques
- Goal: Un compte SQL faible permet de chainer deux linked servers imbriques (EXECUTE AT) pour remonter jusqu'au contexte sa sur une seconde instance, puis xp_cmdshell pour executer des commandes OS.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Connexion avec un compte SQL faible/leake.
2. EXEC sp_linkedservers -> deux liens detectes.
3. EXECUTE('select SUSER_NAME()') at [linked_server_1] -> utilisateur intermediaire.
4. Chainage double: EXECUTE(...) at linked_server_1 contenant un EXECUTE(...) at linked_server_2 -> sa.
5. xp_cmdshell via le contexte sa -> execution OS.
6. SELECT name FROM sys.databases -> base contenant le flag.

## Key Evidence

- le chainage EXECUTE imbrique renvoie SUSER_NAME()='sa' alors que le premier niveau donne seulement un utilisateur intermediaire.

## Dead Ends

- n/a (see Reusable Lessons for pitfalls encountered)

## Payloads And Commands

```text
requetes SQL EXECUTE('...') AT [linked_server] imbriquees (double hop).
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Toujours enumerer sp_linkedservers avant de conclure a une impasse sur une instance SQL peu privilegiee; un chainage a N hops peut escalader silencieusement jusqu'a sa.

## Pattern Candidates

- Nouveau pattern: poo-backtrack-mssql-linked-servers-chain
