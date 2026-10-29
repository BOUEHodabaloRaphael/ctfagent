---
doc_kind: pattern
title: "ThunderCipher Unleashing the Shell 2 - contournement blacklist cat par commandes alternatives"
category: web
slug: unleashing-shell2-blacklist-bypass-altcmd
created: 2026-10-29
status: active
tags:
  - command-injection
  - blacklist-bypass
  - alt-read-commands
  - waf-evasion
chain_summary: "La version corrigee du challenge ne filtre que la commande cat; les commandes alternatives de lecture (head, tac, base64, strings, nl, rev, od) restent fonctionnelles."
---
# ThunderCipher Unleashing the Shell 2 - contournement blacklist cat par commandes alternatives

## Chain Summary

- One-line chain: La version corrigee du challenge ne filtre que la commande cat; les commandes alternatives de lecture (head, tac, base64, strings, nl, rev, od) restent fonctionnelles.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Reponse vide avec cat vs contenu complet du flag avec head sur la meme route.

## Escalation Order

1. POST cmd=cat /flag.txt -> reponse vide (cat filtre).
2. POST cmd=head /flag.txt -> flag retourne en clair.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste (voir lecon ci-dessous).

## Payload Shapes

```text
Memoriser la liste de commandes equivalentes a cat (head, tail, tac, more, less, nl, od, strings, base64, rev) pour tout filtre naif mono-commande.
```

## Related Writeups

- unleashing-shell2-blacklist-bypass-altcmd

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
