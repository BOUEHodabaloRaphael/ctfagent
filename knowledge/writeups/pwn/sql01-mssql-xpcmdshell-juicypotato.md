---
doc_kind: writeup
title: "DANTE SQL01 - MSSQL xp_cmdshell puis JuicyPotato SYSTEM"
category: pwn
slug: sql01-mssql-xpcmdshell-juicypotato
created: 2026-10-29
status: solved
tags:
  - mssql
  - xp_cmdshell
  - juicypotato
  - token-privilege
  - windows-privesc
source: "HTB Pro Lab DANTE"
target: "MSSQL + compte de service avec SeAssignPrimaryTokenPrivilege"
---
# DANTE SQL01 - MSSQL xp_cmdshell puis JuicyPotato SYSTEM

## Challenge Summary

- Source: HTB Pro Lab DANTE
- Target: MSSQL + compte de service avec SeAssignPrimaryTokenPrivilege
- Goal: Creds MSSQL valides activent xp_cmdshell, dont le compte dispose de SeAssignPrimaryTokenPrivilege abusable via JuicyPotato pour impersonner SYSTEM.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. FTP anonyme -> flag initial.
2. Connexion MSSQL avec creds trouvees.
3. EXEC xp_cmdshell 'whoami' -> RCE confirmee.
4. Script sur disque -> mot de passe WinRM additionnel.
5. whoami /priv -> SeAssignPrimaryTokenPrivilege Enabled.
6. JuicyPotato avec CLSID approprie -> SYSTEM.
7. Acces dossier Administrator (ACL stricte) -> flag.

## Key Evidence

- whoami /priv listant SeAssignPrimaryTokenPrivilege Enabled; impersonation SYSTEM confirmee apres JuicyPotato.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
EXEC xp_cmdshell '<cmd>' ; JuicyPotato.exe -l <port> -p <prog> -t * -c {CLSID}.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Tout compte de service avec SeAssignPrimaryTokenPrivilege/SeImpersonatePrivilege + xp_cmdshell => JuicyPotato/PrintSpoofer/GodPotato vers SYSTEM; chercher creds residuels sur disque pour pivoter d'autres services.

## Pattern Candidates

- Voir pattern associe de meme slug.
