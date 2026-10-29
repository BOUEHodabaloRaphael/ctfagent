---
doc_kind: pattern
title: "Evasion de bureau restreint via .bat renomme + AlwaysInstallElevated MSI privesc"
category: pwn
slug: xen-deploy-restricted-desktop-alwaysinstallelevated
created: 2026-10-29
status: active
tags:
  - alwaysinstallelevated
  - restricted-desktop
  - powerup
  - msi-privesc
  - uac-bypass
chain_summary: "Fichier texte renomme en .bat contenant cmd.exe pour contourner un bureau verrouille; AlwaysInstallElevated=1 sur HKCU+HKLM permet un MSI malveillant creant un admin local."
---
# Evasion de bureau restreint via .bat renomme + AlwaysInstallElevated MSI privesc

## Chain Summary

- One-line chain: Fichier texte renomme en .bat contenant cmd.exe pour contourner un bureau verrouille; AlwaysInstallElevated=1 sur HKCU+HKLM permet un MSI malveillant creant un admin local.
- Typical target shape: Session Windows restreinte (Citrix/kiosk) sans acces direct a cmd/powershell/explorer; cle AlwaysInstallElevated potentiellement activee.

## Preconditions

- Session Windows restreinte (Citrix/kiosk) sans acces direct a cmd/powershell/explorer; cle AlwaysInstallElevated potentiellement activee.

## Cheap Probes

- reg query HKCU\Software\Policies\Microsoft\Windows\Installer /v AlwaysInstallElevated et equivalent HKLM.

## Telltale Evidence

- Les deux cles renvoient 0x1.

## Escalation Order

1. Creer un fichier texte, le renommer en .bat contenant cmd.exe pour obtenir un shell.
2. Verifier AlwaysInstallElevated sur HKCU et HKLM.
3. Si 1 des deux cotes, generer un MSI malveillant (PowerUp Write-UserAddMSI) et l'installer.
4. Confirmer la creation d'un compte admin local.

## Common Mistakes

- Abandonner un bureau verrouille sans tester le contournement .bat simple avant de chercher des exploits plus complexes.

## Payload Shapes

```text
Write-UserAddMSI (PowerUp) puis msiexec /i evil.msi
```

## Related Writeups

- xen-deploy-restricted-desktop-alwaysinstallelevated

## Skill Impact

- Related skill: pwn-triage: ajouter le contournement .bat de bureau restreint + check AlwaysInstallElevated systematique apres tout premier acces GUI limite.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
