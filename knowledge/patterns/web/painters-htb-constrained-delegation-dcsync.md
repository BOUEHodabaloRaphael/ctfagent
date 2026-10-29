---
doc_kind: pattern
title: "Zephyr - Painters.htb - Constrained delegation -> S4U -> DCSync -> Domain Admin"
category: web
slug: painters-htb-constrained-delegation-dcsync
created: 2026-10-29
status: active
tags:
  - constrained-delegation
  - s4u2proxy
  - dcsync
  - domain-admin
  - rubeus
chain_summary: "Un compte compromis a une delegation contrainte vers le DC. Rubeus asktgt+s4u impersonne le compte machine DC pour CIFS/HOST/LDAP, permettant un DCSync complet du domaine."
---
# Zephyr - Painters.htb - Constrained delegation -> S4U -> DCSync -> Domain Admin

## Chain Summary

- One-line chain: Un compte compromis a une delegation contrainte vers le DC. Rubeus asktgt+s4u impersonne le compte machine DC pour CIFS/HOST/LDAP, permettant un DCSync complet du domaine.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Rubeus s4u2proxy success; klist montrant les tickets DC$; mimikatz DCSync dump complet.

## Escalation Order

1. Activer RDP via registre+firewall sur la machine cible.
2. RDP comme le compte compromis.
3. Rubeus.exe asktgt puis s4u /impersonateuser:DC$ /altservice:CIFS,HOST,LDAP /ptt.
4. mimikatz lsadump::dcsync /user:<domain>\krbtgt /all /csv -> hashes de tous les comptes.
5. evil-winrm avec le hash Administrator sur le DC.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste.

## Payload Shapes

```text
Constrained delegation + S4U2self/S4U2proxy abuse est une technique cle AD, reutilisable des qu'un compte a une delegation contrainte vers un service sensible.
```

## Related Writeups

- painters-htb-constrained-delegation-dcsync

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
