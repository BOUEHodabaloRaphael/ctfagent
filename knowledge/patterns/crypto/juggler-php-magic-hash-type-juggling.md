---
doc_kind: pattern
title: "ThunderCipher Juggl3r - bypass par magic hash SHA1 0e (PHP type juggling)"
category: crypto
slug: juggler-php-magic-hash-type-juggling
created: 2026-10-29
status: active
tags:
  - php-type-juggling
  - magic-hash-0e
  - loose-comparison
  - sha1-collision
chain_summary: "Le code source expose revele une comparaison lache PHP entre sha1(input) et un sha1 constant de forme 0e+chiffres (interprete comme 0 scientifique); une vraie collision magic-hash est necessaire."
---
# ThunderCipher Juggl3r - bypass par magic hash SHA1 0e (PHP type juggling)

## Chain Summary

- One-line chain: Le code source expose revele une comparaison lache PHP entre sha1(input) et un sha1 constant de forme 0e+chiffres (interprete comme 0 scientifique); une vraie collision magic-hash est necessaire.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Collision de forme (0e+chiffres == 0e+chiffres) entre le hash candidat et le hash cible.

## Escalation Order

1. Recuperation du code source (.bak) -> comparaison == sur un sha1 constant de forme 0e.
2. Calcul du sha1 cible confirmant la forme magique 0e.
3. Test hash[]=1 classique -> echoue dans ce contexte.
4. Recherche dans une liste connue de magic hashes SHA1 0e.
5. Candidat trouve -> collision de forme -> flag retourne.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste (voir lecon ci-dessous).

## Payload Shapes

```text
Garder en memoire une petite liste de magic hashes SHA1/MD5 0e publics pour tout challenge PHP == loose comparison sur un hash.
```

## Related Writeups

- juggler-php-magic-hash-type-juggling

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
