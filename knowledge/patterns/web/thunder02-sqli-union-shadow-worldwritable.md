---
doc_kind: pattern
title: "ThunderCipher Thunder02 - SQLi UNION, craquage SHA256 puis edition directe de /etc/shadow"
category: web
slug: thunder02-sqli-union-shadow-worldwritable
created: 2026-10-29
status: active
tags:
  - sqli-union
  - sha256-crack
  - shadow-world-writable
  - direct-root-overwrite
chain_summary: "Une injection SQL UNION exfiltre les hash SHA256 des comptes; un hash cracke donne un acces SSH limite, mais /etc/shadow est world-writable par erreur, permettant d'ecrire directement un nouveau hash root."
---
# ThunderCipher Thunder02 - SQLi UNION, craquage SHA256 puis edition directe de /etc/shadow

## Chain Summary

- One-line chain: Une injection SQL UNION exfiltre les hash SHA256 des comptes; un hash cracke donne un acces SSH limite, mais /etc/shadow est world-writable par erreur, permettant d'ecrire directement un nouveau hash root.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Permissions world-writable sur /etc/shadow confirmees par ls -la; su root reussi apres reecriture.

## Escalation Order

1. Injection UNION SELECT group_concat(username||':'||password) FROM users.
2. john --format=Raw-SHA256 avec wordlist -> credential cracke.
3. ssh avec ce credential -> ls -la /etc/shadow -> world-writable.
4. Script reecrivant la ligne root: avec un nouveau hash connu.
5. su root -> shell root.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste (voir lecon ci-dessous).

## Payload Shapes

```text
Toujours verifier les permissions effectives de /etc/shadow apres tout acces shell (meme limite): un bit world-writable sur le fichier seul suffit pour une prise de root directe.
```

## Related Writeups

- thunder02-sqli-union-shadow-worldwritable

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
