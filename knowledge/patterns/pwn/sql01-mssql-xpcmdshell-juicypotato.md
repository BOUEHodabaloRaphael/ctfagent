---
doc_kind: pattern
title: "DANTE SQL01 - MSSQL xp_cmdshell puis JuicyPotato SYSTEM"
category: pwn
slug: sql01-mssql-xpcmdshell-juicypotato
created: 2026-10-29
status: active
tags:
  - mssql
  - xp_cmdshell
  - juicypotato
  - token-privilege
  - windows-privesc
chain_summary: "Creds MSSQL valides activent xp_cmdshell, dont le compte dispose de SeAssignPrimaryTokenPrivilege abusable via JuicyPotato pour impersonner SYSTEM."
---
# DANTE SQL01 - MSSQL xp_cmdshell puis JuicyPotato SYSTEM

## Chain Summary

- One-line chain: Creds MSSQL valides activent xp_cmdshell, dont le compte dispose de SeAssignPrimaryTokenPrivilege abusable via JuicyPotato pour impersonner SYSTEM.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- whoami /priv listant SeAssignPrimaryTokenPrivilege Enabled; impersonation SYSTEM confirmee apres JuicyPotato.

## Escalation Order

1. FTP anonyme -> flag initial.
2. Connexion MSSQL avec creds trouvees.
3. EXEC xp_cmdshell 'whoami' -> RCE confirmee.
4. Script sur disque -> mot de passe WinRM additionnel.
5. whoami /priv -> SeAssignPrimaryTokenPrivilege Enabled.
6. JuicyPotato avec CLSID approprie -> SYSTEM.
7. Acces dossier Administrator (ACL stricte) -> flag.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste (voir lecon ci-dessous).

## Payload Shapes

```text
Tout compte de service avec SeAssignPrimaryTokenPrivilege/SeImpersonatePrivilege + xp_cmdshell => JuicyPotato/PrintSpoofer/GodPotato vers SYSTEM; chercher creds residuels sur disque pour pivoter d'autres services.
```

## Related Writeups

- sql01-mssql-xpcmdshell-juicypotato

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
