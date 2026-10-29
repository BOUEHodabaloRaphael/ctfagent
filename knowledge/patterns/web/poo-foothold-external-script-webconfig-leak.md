---
doc_kind: pattern
title: "sp_execute_external_script pour changer de contexte d'execution et contourner un refus NTFS"
category: web
slug: poo-foothold-external-script-webconfig-leak
created: 2026-10-29
status: active
tags:
  - mssql
  - sp_execute_external_script
  - web-config-leak
  - http-basic-auth
  - context-switch
chain_summary: "Quand xp_cmdshell ou une lecture directe de fichier est refusee pour le contexte du compte SQL, sp_execute_external_script (R/Python) execute sous un autre contexte utilisateur OS qui peut avoir des droits differents."
---
# sp_execute_external_script pour changer de contexte d'execution et contourner un refus NTFS

## Chain Summary

- One-line chain: Quand xp_cmdshell ou une lecture directe de fichier est refusee pour le contexte du compte SQL, sp_execute_external_script (R/Python) execute sous un autre contexte utilisateur OS qui peut avoir des droits differents.
- Typical target shape: MSSQL avec Machine Learning Services (R/Python) active; une lecture de fichier echoue avec le contexte SQL standard.

## Preconditions

- MSSQL avec Machine Learning Services (R/Python) active; une lecture de fichier echoue avec le contexte SQL standard.

## Cheap Probes

- Comparer le resultat d'une lecture de fichier via xp_cmdshell vs via sp_execute_external_script sur le meme chemin.

## Telltale Evidence

- La lecture reussit via sp_execute_external_script alors qu'elle echouait via xp_cmdshell/openrowset.

## Escalation Order

1. Confirmer que sp_execute_external_script est active (R ou Python).
2. Ecrire un script minimal lisant le fichier cible et renvoyant son contenu via le resultset SQL.
3. Executer et recuperer le contenu.
4. Chercher des credentials dans des commentaires/blocs desactives du fichier.

## Common Mistakes

- Conclure a un acces refuse definitif sur un fichier apres un seul contexte d'execution testé (xp_cmdshell) sans essayer les autres (external script).

## Payload Shapes

```text
EXEC sp_execute_external_script @language=N'Python', @script=N'OutputDataSet = pandas.DataFrame([open(path).read()])'
```

## Related Writeups

- poo-foothold-external-script-webconfig-leak

## Skill Impact

- Related skill: web-triage (MSSQL): ajouter sp_execute_external_script comme contexte alternatif de lecture de fichier quand xp_cmdshell/openrowset echouent.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
