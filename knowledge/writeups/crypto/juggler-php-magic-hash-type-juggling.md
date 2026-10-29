---
doc_kind: writeup
title: "ThunderCipher Juggl3r - bypass par magic hash SHA1 0e (PHP type juggling)"
category: crypto
slug: juggler-php-magic-hash-type-juggling
created: 2026-10-29
status: solved
tags:
  - php-type-juggling
  - magic-hash-0e
  - loose-comparison
  - sha1-collision
source: thundercipher.in/labs
target: "Comparaison lache PHP (==) sur un hash SHA1"
---
# ThunderCipher Juggl3r - bypass par magic hash SHA1 0e (PHP type juggling)

## Challenge Summary

- Source: thundercipher.in/labs
- Target: Comparaison lache PHP (==) sur un hash SHA1
- Goal: Le code source expose revele une comparaison lache PHP entre sha1(input) et un sha1 constant de forme 0e+chiffres (interprete comme 0 scientifique); une vraie collision magic-hash est necessaire.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Recuperation du code source (.bak) -> comparaison == sur un sha1 constant de forme 0e.
2. Calcul du sha1 cible confirmant la forme magique 0e.
3. Test hash[]=1 classique -> echoue dans ce contexte.
4. Recherche dans une liste connue de magic hashes SHA1 0e.
5. Candidat trouve -> collision de forme -> flag retourne.

## Key Evidence

- Collision de forme (0e+chiffres == 0e+chiffres) entre le hash candidat et le hash cible.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
Chaine candidate issue d'une liste de magic hashes PHP connus (type juggling 0e).
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Garder en memoire une petite liste de magic hashes SHA1/MD5 0e publics pour tout challenge PHP == loose comparison sur un hash.

## Pattern Candidates

- Voir pattern associe de meme slug.
