---
doc_kind: pattern
title: "Zephyr - zsm.local - MSSQL impersonation SA + xp_cmdshell + SweetPotato"
category: pwn
slug: zephyr-zsm-local-mssql-impersonation-sweetpotato
created: 2026-10-29
status: active
tags:
  - mssql
  - powerupsql
  - impersonation
  - xp_cmdshell
  - sweetpotato
  - seimpersonateprivilege
chain_summary: "Des credentials reutilisees donnent acces a MSSQL. PowerUpSQL identifie un droit d'impersonation sur sa (sysadmin), exploite pour activer xp_cmdshell et obtenir un reverse shell, puis SweetPotato (SeImpersonatePrivilege) donne SYSTEM."
---
# Zephyr - zsm.local - MSSQL impersonation SA + xp_cmdshell + SweetPotato

## Chain Summary

- One-line chain: Des credentials reutilisees donnent acces a MSSQL. PowerUpSQL identifie un droit d'impersonation sur sa (sysadmin), exploite pour activer xp_cmdshell et obtenir un reverse shell, puis SweetPotato (SeImpersonatePrivilege) donne SYSTEM.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- PowerUpSQL confirme IsExploitable: Yes; xp_cmdshell whoami confirme le compte de service; SweetPotato confirme la creation du process; getuid confirme SYSTEM.

## Escalation Order

1. nmap confirme MSSQL.
2. Upload PowerUpSQL.ps1, Invoke-SQLAudit -> droit d'impersonation sur sa trouve.
3. EXECUTE AS LOGIN='sa'; EXEC sp_addsrvrolemember pour s'ajouter a sysadmin.
4. Activation xp_cmdshell (sp_configure).
5. Reverse shell via xp_cmdshell.
6. whoami /priv montre SeImpersonatePrivilege.
7. SweetPotato.exe -> SYSTEM.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste.

## Payload Shapes

```text
Chaine SQL impersonation SA -> sysadmin -> xp_cmdshell -> SeImpersonatePrivilege -> SweetPotato est un pattern tres standard contre MSSQL.
```

## Related Writeups

- zephyr-zsm-local-mssql-impersonation-sweetpotato

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
