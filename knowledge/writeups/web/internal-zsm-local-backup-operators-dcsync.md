---
doc_kind: writeup
title: "Zephyr - internal domain - Abus Backup Operators -> dump distant ruches DC -> DCSync"
category: web
slug: internal-zsm-local-backup-operators-dcsync
created: 2026-10-29
status: solved
tags:
  - backup-operators
  - sebackupprivilege
  - dcsync
  - secretsdump
  - domain-admin
source: "HTB Pro Lab Zephyr"
target: "Compte membre de Backup Operators + DC du second domaine"
---
# Zephyr - internal domain - Abus Backup Operators -> dump distant ruches DC -> DCSync

## Challenge Summary

- Source: HTB Pro Lab Zephyr
- Target: Compte membre de Backup Operators + DC du second domaine
- Goal: Un compte compromis est membre de Backup Operators. Apres upgrade vers un shell veritablement interactif (requis pour SeBackupPrivilege), un outil dedie dump a distance les ruches du DC vers un serveur SMB local, permettant un DCSync complet.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. BloodHound: compte membre de Backup Operators.
2. Acces au partage C$ du DC refuse avec un shell non-interactif.
3. Shell interactif (logon de type 2) resout le probleme.
4. Upload d'un outil de dump distant des ruches via SeBackupPrivilege.
5. Serveur SMB local pour recevoir les ruches.
6. Dump des ruches SAM/SECURITY/SYSTEM du DC -> hash du compte machine DC.
7. secretsdump.py local sur les ruches puis DCSync avec le hash machine -> hash Administrator.
8. evil-winrm avec le hash admin sur le DC.

## Key Evidence

- Confirmation du dump des ruches vers le serveur SMB local; secretsdump confirme l'utilisation de la methode DRSUAPI pour les secrets NTDS.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
Outil de dump distant via SeBackupPrivilege, impacket-smbserver, secretsdump.py.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout (lecture visuelle verifiee).

## Reusable Lessons

- Abus de Backup Operators via SeBackupPrivilege pour exfiltrer les ruches registre du DC a distance et DCSync est une technique puissante et peu connue; necessite un shell veritablement interactif (pas un reverse shell basique) pour que le privilege s'applique correctement.

## Pattern Candidates

- Voir pattern associe de meme slug.
