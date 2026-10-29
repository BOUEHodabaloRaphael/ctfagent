---
doc_kind: pattern
title: "DANTE NIX04 - SQLi error-based MariaDB puis bypass sudo -u#-1"
category: web
slug: nix04-sqli-errorbased-sudo-uid-bypass
created: 2026-10-29
status: active
tags:
  - sqli-error-based
  - sqlmap
  - extractvalue
  - sudo-uid-bypass
  - mariadb
chain_summary: "Injection SQL error-based (EXTRACTVALUE) sur un parametre pour dump rapide; creds applicatifs donnent un acces avec sudo NOPASSWD /bin/bash, contourne via sudo -u#-1 (UID -1 = 4294967295 = root)."
---
# DANTE NIX04 - SQLi error-based MariaDB puis bypass sudo -u#-1

## Chain Summary

- One-line chain: Injection SQL error-based (EXTRACTVALUE) sur un parametre pour dump rapide; creds applicatifs donnent un acces avec sudo NOPASSWD /bin/bash, contourne via sudo -u#-1 (UID -1 = 4294967295 = root).

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Message d'erreur MariaDB confirmant l'injection; sortie sqlmap confirmant error-based (EXTRACTVALUE) injectable.

## Escalation Order

1. Parametre GET -> erreur SQL MariaDB confirmant l'injection.
2. sqlmap --technique=BEUSTQ --dbs confirme injectable.
3. sqlmap --technique=E --string=<marqueur> pour dump direct via EXTRACTVALUE -> flag.
4. Creds applicatifs trouves en base.
5. sudo -l -> (ALL) NOPASSWD: /bin/bash.
6. sudo -u#-1 root (UID -1 interprete comme root) -> shell root.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste (voir lecon ci-dessous).

## Payload Shapes

```text
Error-based EXTRACTVALUE permet un dump direct sans --dbs/--dump (gain de temps); sudo -u#<valeur negative> est une technique de bypass UID classique quand NOPASSWD est mal restreint.
```

## Related Writeups

- nix04-sqli-errorbased-sudo-uid-bypass

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
