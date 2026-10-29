---
doc_kind: writeup
title: "Endgame XEN - Owned (SeBackupPrivilege -> dump NTDS -> Domain Admin)"
category: misc
slug: xen-owned-sebackupprivilege-ntds-dump
created: 2026-10-29
status: solved
tags:
  - sebackupprivilege
  - ntds-dit
  - secretsdump
  - backup-operators
  - domain-admin
source: "HTB Endgame XEN"
target: "DC avec compte Backup Operators"
---
# Endgame XEN - Owned (SeBackupPrivilege -> dump NTDS -> Domain Admin)

## Challenge Summary

- Source: HTB Endgame XEN
- Target: DC avec compte Backup Operators
- Goal: Le compte backup-svc, membre de Backup Operators, utilise SeBackupPrivilege pour copier ntds.dit verrouille sans alerte, puis secretsdump recupere le hash Administrator pour un pass-the-hash final.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. whoami /priv confirme SeBackupPrivilege/SeRestorePrivilege Enabled (groupe Backup Operators).
2. Copy-FileSeBackupPrivilege copie ntds.dit malgre le verrou de fichier vers un partage distant.
3. reg save hklm\system exporte la ruche SYSTEM necessaire au dechiffrement.
4. secretsdump.py -system -ntds ... LOCAL extrait tous les hashs NTLM du domaine.
5. wmiexec.py avec le hash Administrator -> shell SYSTEM/DA sur le DC -> flag final.

## Key Evidence

- secretsdump affiche le hash Administrator extrait du ntds.dit copie malgre verrouillage.

## Dead Ends

- n/a (see Reusable Lessons for pitfalls encountered)

## Payloads And Commands

```text
copie de fichier verrouille via abus de privilege (SeBackupPrivilege) + secretsdump offline.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Appartenir a Backup Operators = exfiltration ntds.dit sans toucher au service NTDS ni declencher DCSync; toujours verifier whoami /priv apres chaque nouvel acces, meme limite.

## Pattern Candidates

- Nouveau pattern: xen-owned-sebackupprivilege-ntds-dump
