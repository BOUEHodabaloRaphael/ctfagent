---
doc_kind: pattern
title: "SeBackupPrivilege pour exfiltrer ntds.dit sans DCSync"
category: misc
slug: xen-owned-sebackupprivilege-ntds-dump
created: 2026-10-29
status: active
tags:
  - sebackupprivilege
  - ntds-dit
  - secretsdump
  - backup-operators
  - domain-admin
chain_summary: "Un compte membre de Backup Operators (SeBackupPrivilege) peut copier ntds.dit verrouille directement, sans declencher d'alerte DCSync, puis le dechiffrer offline avec la ruche SYSTEM."
---
# SeBackupPrivilege pour exfiltrer ntds.dit sans DCSync

## Chain Summary

- One-line chain: Un compte membre de Backup Operators (SeBackupPrivilege) peut copier ntds.dit verrouille directement, sans declencher d'alerte DCSync, puis le dechiffrer offline avec la ruche SYSTEM.
- Typical target shape: Acces a un compte Windows avec SeBackupPrivilege active (souvent via Backup Operators).

## Preconditions

- Acces a un compte Windows avec SeBackupPrivilege active (souvent via Backup Operators).

## Cheap Probes

- whoami /priv systematiquement apres chaque nouvel acces, meme limite.

## Telltale Evidence

- SeBackupPrivilege et SeRestorePrivilege apparaissent Enabled.

## Escalation Order

1. Confirmer SeBackupPrivilege via whoami /priv.
2. Copier ntds.dit malgre le verrou via un outil exploitant ce privilege (Copy-FileSeBackupPrivilege ou equivalent).
3. Exporter la ruche SYSTEM (reg save).
4. secretsdump.py offline pour extraire tous les hashs NTLM.
5. Pass-the-hash avec le hash Administrator obtenu.

## Common Mistakes

- Chercher DCSync (qui peut etre detecte/alerte) alors que SeBackupPrivilege permet une exfiltration plus discrete du meme fichier.

## Payload Shapes

```text
secretsdump.py -sam SAM -system SYSTEM -ntds ntds.dit LOCAL
```

## Related Writeups

- xen-owned-sebackupprivilege-ntds-dump

## Skill Impact

- Related skill: pwn-triage/AD: ajouter whoami /priv systematique + SeBackupPrivilege->ntds.dit comme chemin de domain admin discret.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
