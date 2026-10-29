---
doc_kind: pattern
title: "DANTE NIX02 - reutilisation de cle SSH root pivot"
category: misc
slug: nix02-ssh-key-reuse
created: 2026-10-29
status: active
tags:
  - ssh-key-reuse
  - pivot
  - credential-reuse
  - lateral-movement
chain_summary: "La cle privee root recuperee sur une machine est reutilisee directement pour un acces root SSH sur une autre, sans exploitation additionnelle."
---
# DANTE NIX02 - reutilisation de cle SSH root pivot

## Chain Summary

- One-line chain: La cle privee root recuperee sur une machine est reutilisee directement pour un acces root SSH sur une autre, sans exploitation additionnelle.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Connexion SSH root reussie sans mot de passe via la cle deja obtenue sur une autre machine.

## Escalation Order

1. ssh -i <cle-dejaobtenue> root@<autre-machine>.
2. Acces root immediat, lecture des flags.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste (voir lecon ci-dessous).

## Payload Shapes

```text
Toujours retester une cle/credential root valide sur l'ensemble du range interne avant d'investir dans une nouvelle exploitation.
```

## Related Writeups

- nix02-ssh-key-reuse

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
