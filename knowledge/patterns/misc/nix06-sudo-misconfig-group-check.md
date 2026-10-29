---
doc_kind: pattern
title: "DANTE NIX06 - credentials reutilises puis regle sudo permissive"
category: misc
slug: nix06-sudo-misconfig-group-check
created: 2026-10-29
status: active
tags:
  - sudo-misconfig
  - credential-harvesting
  - desktop-files
  - lateral-movement
chain_summary: "Acces initial via creds deja obtenus sur une autre machine, puis un second compte (trouve via un fichier Desktop) beneficie d'une regle sudo trop permissive menant directement a root."
---
# DANTE NIX06 - credentials reutilises puis regle sudo permissive

## Chain Summary

- One-line chain: Acces initial via creds deja obtenus sur une autre machine, puis un second compte (trouve via un fichier Desktop) beneficie d'une regle sudo trop permissive menant directement a root.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- sudo -i reussissant sans restriction, acces root confirme.

## Escalation Order

1. Creds deja obtenus -> flag user.
2. Fichier Desktop -> creds d'un autre service exposes.
3. Creds web d'un second compte.
4. sudo -l -> regle permettant sudo -i direct -> root -> flag admin.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste (voir lecon ci-dessous).

## Payload Shapes

```text
Toujours verifier les fichiers Desktop/documents residuels pour des credentials d'autres comptes, et systematiquement lancer sudo -l sur chaque nouveau compte obtenu.
```

## Related Writeups

- nix06-sudo-misconfig-group-check

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
