---
doc_kind: writeup
title: "HTB Endgame RPG — Ch.5 WinSCP creds + proxy.pac empoisonne + crack NTLMv2"
category: misc
slug: rpg-ch5-winscp-responder-ntlm-relay-crack
created: 2026-10-29
status: solved
tags:
  - ntlmv2-capture
  - responder
  - proxy-pac-poisoning
  - winscp-creds
  - runascs
  - hashcat
source: "HackTheBox Endgame RPG"
target: "Registre WinSCP + proxy.pac partage en ecriture (machine Lux/Gelus)"
---
# HTB Endgame RPG — Ch.5 WinSCP creds + proxy.pac empoisonne + crack NTLMv2

## Challenge Summary

- Source: HackTheBox Endgame RPG
- Target: Registre WinSCP + proxy.pac partage en ecriture (machine Lux/Gelus)
- Goal: PtH vers Lux pour extraire des credentials WinSCP obfusques depuis le registre, contournement d'un verrou d'execution PowerShell via RunasCs, puis empoisonnement d'un proxy.pac partage en ecriture pour forcer une auth NTLMv2 capturee par Responder et crackee offline.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Reutilisation du hash SAM Administrator de Lux en Pass-the-Hash.
2. Fichier de seed WinSCP trouve dans un autre profil -> credentials dans le registre, export NTUSER.DAT et lecture offline.
3. Champ Password obfusque (pas chiffre) -> decodage avec l'algorithme WinSCP connu.
4. Aucune methode PowerShell classique n'execute dans le contexte cible -> RunasCs (CreateProcess Win32 direct).
5. L'utilisateur cible a droit d'ecriture sur un fichier proxy.pac partage -> remplacement pour forcer le trafic proxy vers l'attaquant.
6. Responder en mode proxy (-P) -> reception de requetes Net-NTLMv2 d'un compte de service.
7. Relais impossible (patch applique) -> crack offline hashcat mode 5600.
8. WinRM avec les credentials obtenus -> lecture du flag en admin local de Gelus.

## Key Evidence

- "winscppasswd -> credentials decodes"; "hashcat -m 5600 -> compte:motdepasse"; "evil-winrm -> flag.txt lu".

## Dead Ends

- Relais NTLM direct impossible car le correctif pertinent etait deja applique - oblige a cracker offline plutot que relayer.

## Payloads And Commands

```text
proxy.pac empoisonne (FindProxyForURL -> IP attaquant) + capture Responder (-P) + crack hashcat mode 5600.
```

## Flag / Outcome

- Flag lu en admin local de Gelus.

## Reusable Lessons

- Tout fichier de config client partage en ecriture (proxy.pac, fichier de connexion) peut etre detourne pour forcer une auth reseau capturable par Responder, surtout quand le relais direct est patche et qu'il faut casser le hash offline.

## Pattern Candidates

- Nouveau pattern: shared-config-file-ntlm-capture
