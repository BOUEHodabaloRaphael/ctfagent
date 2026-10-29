---
doc_kind: writeup
title: "Zephyr - zsm.local - MSSQL impersonation SA + xp_cmdshell + SweetPotato"
category: pwn
slug: zephyr-zsm-local-mssql-impersonation-sweetpotato
created: 2026-10-29
status: solved
tags:
  - mssql
  - powerupsql
  - impersonation
  - xp_cmdshell
  - sweetpotato
  - seimpersonateprivilege
source: "HTB Pro Lab Zephyr"
target: "MSSQL Server avec droit d'impersonation sur sa"
---
# Zephyr - zsm.local - MSSQL impersonation SA + xp_cmdshell + SweetPotato

## Challenge Summary

- Source: HTB Pro Lab Zephyr
- Target: MSSQL Server avec droit d'impersonation sur sa
- Goal: Des credentials reutilisees donnent acces a MSSQL. PowerUpSQL identifie un droit d'impersonation sur sa (sysadmin), exploite pour activer xp_cmdshell et obtenir un reverse shell, puis SweetPotato (SeImpersonatePrivilege) donne SYSTEM.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. nmap confirme MSSQL.
2. Upload PowerUpSQL.ps1, Invoke-SQLAudit -> droit d'impersonation sur sa trouve.
3. EXECUTE AS LOGIN='sa'; EXEC sp_addsrvrolemember pour s'ajouter a sysadmin.
4. Activation xp_cmdshell (sp_configure).
5. Reverse shell via xp_cmdshell.
6. whoami /priv montre SeImpersonatePrivilege.
7. SweetPotato.exe -> SYSTEM.

## Key Evidence

- PowerUpSQL confirme IsExploitable: Yes; xp_cmdshell whoami confirme le compte de service; SweetPotato confirme la creation du process; getuid confirme SYSTEM.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
PowerUpSQL.ps1 (Invoke-SQLAudit, Get-SQLQuery), xp_cmdshell, SweetPotato.exe.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout (lecture visuelle verifiee).

## Reusable Lessons

- Chaine SQL impersonation SA -> sysadmin -> xp_cmdshell -> SeImpersonatePrivilege -> SweetPotato est un pattern tres standard contre MSSQL.

## Pattern Candidates

- Voir pattern associe de meme slug.
