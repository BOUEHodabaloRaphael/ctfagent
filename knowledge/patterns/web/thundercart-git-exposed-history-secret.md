---
doc_kind: pattern
title: "ThunderCipher ThunderCart - .git expose, secret dans une revision anterieure"
category: web
slug: thundercart-git-exposed-history-secret
created: 2026-10-29
status: active
tags:
  - git-exposed
  - git-dumper
  - commit-history-secret
  - flask-secretkey-base32
chain_summary: "Le dossier .git est expose publiquement; le flag.txt du HEAD est un leurre REDACTED, le vrai secret se trouve dans une revision anterieure, et une cle Flask est encodee en base32."
---
# ThunderCipher ThunderCart - .git expose, secret dans une revision anterieure

## Chain Summary

- One-line chain: Le dossier .git est expose publiquement; le flag.txt du HEAD est un leurre REDACTED, le vrai secret se trouve dans une revision anterieure, et une cle Flask est encodee en base32.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Difference de contenu de flag.txt entre HEAD (leurre) et une revision anterieure contenant la vraie valeur.

## Escalation Order

1. Detection .git expose publiquement.
2. git-dumper pour exfiltrer le depot complet localement.
3. git log/show sur chaque commit -> flag.txt du HEAD = leurre.
4. Recherche dans les revisions anterieures -> vrai secret trouve.
5. Decodage base32 de la cle Flask trouvee dans le code.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste (voir lecon ci-dessous).

## Payload Shapes

```text
Un .git expose doit etre audite sur TOUT son historique (git log --all), pas seulement le HEAD: les auteurs corrigent souvent juste le dernier commit.
```

## Related Writeups

- thundercart-git-exposed-history-secret

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
