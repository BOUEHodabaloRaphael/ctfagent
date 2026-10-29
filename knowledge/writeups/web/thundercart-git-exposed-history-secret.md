---
doc_kind: writeup
title: "ThunderCipher ThunderCart - .git expose, secret dans une revision anterieure"
category: web
slug: thundercart-git-exposed-history-secret
created: 2026-10-29
status: solved
tags:
  - git-exposed
  - git-dumper
  - commit-history-secret
  - flask-secretkey-base32
source: thundercipher.in/labs
target: "Depot .git expose publiquement"
---
# ThunderCipher ThunderCart - .git expose, secret dans une revision anterieure

## Challenge Summary

- Source: thundercipher.in/labs
- Target: Depot .git expose publiquement
- Goal: Le dossier .git est expose publiquement; le flag.txt du HEAD est un leurre REDACTED, le vrai secret se trouve dans une revision anterieure, et une cle Flask est encodee en base32.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Detection .git expose publiquement.
2. git-dumper pour exfiltrer le depot complet localement.
3. git log/show sur chaque commit -> flag.txt du HEAD = leurre.
4. Recherche dans les revisions anterieures -> vrai secret trouve.
5. Decodage base32 de la cle Flask trouvee dans le code.

## Key Evidence

- Difference de contenu de flag.txt entre HEAD (leurre) et une revision anterieure contenant la vraie valeur.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
git-dumper <url>/.git/ <dossier>; git log --all puis git show <commit>:<fichier>; base32 -d.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Un .git expose doit etre audite sur TOUT son historique (git log --all), pas seulement le HEAD: les auteurs corrigent souvent juste le dernier commit.

## Pattern Candidates

- Voir pattern associe de meme slug.
