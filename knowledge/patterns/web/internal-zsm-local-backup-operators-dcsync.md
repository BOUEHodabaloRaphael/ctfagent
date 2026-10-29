---
doc_kind: pattern
title: "Zephyr - internal domain - Abus Backup Operators -> dump distant ruches DC -> DCSync"
category: web
slug: internal-zsm-local-backup-operators-dcsync
created: 2026-10-29
status: active
tags:
  - backup-operators
  - sebackupprivilege
  - dcsync
  - secretsdump
  - domain-admin
chain_summary: "Un compte compromis est membre de Backup Operators. Apres upgrade vers un shell veritablement interactif (requis pour SeBackupPrivilege), un outil dedie dump a distance les ruches du DC vers un serveur SMB local, permettant un DCSync complet."
---
# Zephyr - internal domain - Abus Backup Operators -> dump distant ruches DC -> DCSync

## Chain Summary

- One-line chain: Un compte compromis est membre de Backup Operators. Apres upgrade vers un shell veritablement interactif (requis pour SeBackupPrivilege), un outil dedie dump a distance les ruches du DC vers un serveur SMB local, permettant un DCSync complet.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Confirmation du dump des ruches vers le serveur SMB local; secretsdump confirme l'utilisation de la methode DRSUAPI pour les secrets NTDS.

## Escalation Order

1. BloodHound: compte membre de Backup Operators.
2. Acces au partage C$ du DC refuse avec un shell non-interactif.
3. Shell interactif (logon de type 2) resout le probleme.
4. Upload d'un outil de dump distant des ruches via SeBackupPrivilege.
5. Serveur SMB local pour recevoir les ruches.
6. Dump des ruches SAM/SECURITY/SYSTEM du DC -> hash du compte machine DC.
7. secretsdump.py local sur les ruches puis DCSync avec le hash machine -> hash Administrator.
8. evil-winrm avec le hash admin sur le DC.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste.

## Payload Shapes

```text
Abus de Backup Operators via SeBackupPrivilege pour exfiltrer les ruches registre du DC a distance et DCSync est une technique puissante et peu connue; necessite un shell veritablement interactif (pas un reverse shell basique) pour que le privilege s'applique correctement.
```

## Related Writeups

- internal-zsm-local-backup-operators-dcsync

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
