---
doc_kind: pattern
title: "Splunk ShellSplunk RCE + PostgreSQL trust COPY FROM PROGRAM pour exfiltration de fichiers"
category: web
slug: offshore-splunk-shellsplunk-postgres-copy-program-exfil
created: 2026-10-30
status: active
tags:
  - legacy-memory-migration
  - nctf26-prep
  - offshore
chain_summary: "Une app Splunk sans scripted inputs utilisables (bloques) mais avec l'app tierce ShellSplunk deja installee donne RCE via des commandes de recherche custom; separement, un PostgreSQL local en mode trust permet d'exfiltrer n'importe quel fichier lisible via COPY <table> FROM PROGRAM 'cat fichier' (PAS TO PROGRAM, dont la sortie n'est jamais renvoyee)."
---
# Splunk ShellSplunk RCE + PostgreSQL trust COPY FROM PROGRAM pour exfiltration de fichiers

## Chain Summary

- One-line chain: Une app Splunk sans scripted inputs utilisables (bloques) mais avec l'app tierce ShellSplunk deja installee donne RCE via des commandes de recherche custom; separement, un PostgreSQL local en mode trust permet d'exfiltrer n'importe quel fichier lisible via COPY <table> FROM PROGRAM 'cat fichier' (PAS TO PROGRAM, dont la sortie n'est jamais renvoyee).

## Preconditions

- Instance Splunk avec l'app ShellSplunk (ou equivalent) deja presente; PostgreSQL local accessible en mode trust (aucun mot de passe demande) depuis le compte applicatif courant.

## Cheap Probes

- Chercher /opt/splunk/etc/apps/<nom_app>/default/commands.conf pour des commandes de recherche custom type bindshell/revshell.

## Telltale Evidence

- psql -h 127.0.0.1 -U postgres -d postgres fonctionne sans mot de passe meme sous un compte OS qui n'est pas 'postgres' au niveau PostgreSQL, si pg_hba.conf est en trust local.

## Escalation Order

1. Si scripted inputs/transforms.conf externes sont bloques par le lab, chercher une app tierce de reverse shell deja installee (ShellSplunk ou equivalent) dans etc/apps/*/default/commands.conf.
2. Executer | bindshell ou | revshell via l'interface de recherche Splunk pour obtenir un shell dans le contexte du compte Splunk (souvent pas 'splunk' lui-meme mais l'utilisateur ayant installe l'app).
3. Tester PostgreSQL local en trust: psql -h 127.0.0.1 -U postgres -d postgres sans mot de passe.
4. pg_read_file() echoue generalement sur un chemin absolu (PG9.6+: 'absolute path not allowed') — impasse directe.
5. COPY (...) TO PROGRAM 'cmd' n'exfiltre RIEN (la sortie du programme n'est pas renvoyee au client, seul 'COPY N' est confirme) — impasse aussi.
6. COPY <table_temporaire> FROM PROGRAM 'cat fichier' fonctionne: la sortie du programme devient des LIGNES SQL dans la table, exfiltrant ainsi n'importe quel fichier lisible par l'utilisateur postgres OS.

## Common Mistakes

- Utiliser COPY TO PROGRAM en pensant exfiltrer un fichier (la sortie n'est jamais renvoyee) au lieu de COPY FROM PROGRAM qui capture bien la sortie comme des lignes de table.

## Payload Shapes

```text
CREATE TEMP TABLE t(line text); COPY t FROM PROGRAM 'cat /chemin/fichier'; SELECT * FROM t;
```

## Related Writeups

- N/A

## Skill Impact

- Related skill: web-triage (PostgreSQL): ajouter le piege TO PROGRAM (inutile) vs FROM PROGRAM (exfiltration reelle) comme reflexe systematique sur tout acces PostgreSQL superuser en trust.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
