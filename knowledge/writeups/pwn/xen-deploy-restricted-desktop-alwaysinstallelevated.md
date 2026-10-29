---
doc_kind: writeup
title: "Endgame XEN - Deploy (evasion bureau restreint + AlwaysInstallElevated)"
category: pwn
slug: xen-deploy-restricted-desktop-alwaysinstallelevated
created: 2026-10-29
status: solved
tags:
  - alwaysinstallelevated
  - restricted-desktop
  - powerup
  - msi-privesc
  - uac-bypass
source: "HTB Endgame XEN"
target: "Bureau Windows restreint (Citrix session)"
---
# Endgame XEN - Deploy (evasion bureau restreint + AlwaysInstallElevated)

## Challenge Summary

- Source: HTB Endgame XEN
- Target: Bureau Windows restreint (Citrix session)
- Goal: Contournement d'un bureau Citrix verrouille via un .bat renomme pour lancer cmd.exe, puis abus de la cle de registre AlwaysInstallElevated (HKCU+HKLM=1) pour installer un MSI malveillant creant un admin local, suivi d'un bypass UAC.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Menu Demarrer/Explorer verrouilles sur C:\Windows\System32, pas de cmd/powershell direct.
2. Creer un Document texte, le renommer cmd.bat avec contenu 'cmd.exe' -> execution via clic.
3. Partage SMB depuis Kali (smbserver.py) pour livrer nc64.exe, reverse shell.
4. reg query HKCU/HKLM AlwaysInstallElevated -> 0x1 des deux cotes.
5. PowerUp Write-UserAddMSI genere un MSI qui cree un utilisateur admin local a l'installation.
6. Bypass UAC (.NET charge par reflexion) pour obtenir un cmd.exe reellement eleve.

## Key Evidence

- reg query renvoie AlwaysInstallElevated REG_DWORD 0x1 sur HKCU et HKLM simultanement.

## Dead Ends

- n/a (see Reusable Lessons for pitfalls encountered)

## Payloads And Commands

```text
fichier .bat renomme + MSI malveillant (PowerUp Write-UserAddMSI).
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Sur un desktop restreint sans cmd/explorer, un .txt renomme en .bat contenant cmd.exe est un contournement fiable; AlwaysInstallElevated=1 sur HKCU+HKLM est un privesc Windows direct via MSI.

## Pattern Candidates

- Nouveau pattern: xen-deploy-restricted-desktop-alwaysinstallelevated
