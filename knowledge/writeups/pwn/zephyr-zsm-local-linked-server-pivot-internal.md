---
doc_kind: writeup
title: "Zephyr - zsm.local - Pivot via linked SQL server vers un second domaine"
category: pwn
slug: zephyr-zsm-local-linked-server-pivot-internal
created: 2026-10-29
status: solved
tags:
  - mssql
  - linked-server
  - cross-domain-pivot
  - sweetpotato
source: "HTB Pro Lab Zephyr"
target: "MSSQL avec linked server vers un serveur d'un autre domaine"
---
# Zephyr - zsm.local - Pivot via linked SQL server vers un second domaine

## Challenge Summary

- Source: HTB Pro Lab Zephyr
- Target: MSSQL avec linked server vers un serveur d'un autre domaine
- Goal: sp_linkedservers revele un lien vers un serveur SQL d'un second domaine; les requetes sont executees a distance via EXECUTE AT, permettant de repeter la chaine xp_cmdshell+SweetPotato sur ce second serveur.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. EXEC sp_linkedservers -> second serveur decouvert.
2. EXECUTE AS LOGIN='sa'; EXECUTE('select @@servername;') at [linked_server] confirme le pivot.
3. Meme chaine xp_cmdshell via syntaxe linked server.
4. whoami confirme le franchissement vers le 2e domaine.
5. Reverse shell, SeImpersonatePrivilege confirme, SweetPotato -> SYSTEM.

## Key Evidence

- sp_linkedservers listing; whoami output confirmant le changement de domaine.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
MSSQL linked server EXECUTE AT syntax, xp_cmdshell, SweetPotato.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout (lecture visuelle verifiee).

## Reusable Lessons

- Pivot via serveurs SQL lies (linked servers) est une technique de mouvement lateral/cross-domain sous-estimee, a toujours tester apres un acces sysadmin sur une instance MSSQL.

## Pattern Candidates

- Voir pattern associe de meme slug.
