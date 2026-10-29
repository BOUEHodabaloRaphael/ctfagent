---
doc_kind: pattern
title: "ThunderCipher Client Side - script JSFuck execute en Node.js pour reveler le flag"
category: crypto
slug: clientside-jsfuck-nodejs-decode
created: 2026-10-29
status: active
tags:
  - jsfuck
  - js-obfuscation
  - nodejs-execution
  - client-side-secret
chain_summary: "robots.txt pointe vers un script JS obfusque en JSFuck (uniquement les caracteres []()!+); son execution directe sous Node.js revele le flag en clair."
---
# ThunderCipher Client Side - script JSFuck execute en Node.js pour reveler le flag

## Chain Summary

- One-line chain: robots.txt pointe vers un script JS obfusque en JSFuck (uniquement les caracteres []()!+); son execution directe sous Node.js revele le flag en clair.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Sortie console Node.js affichant directement le flag apres execution du blob JSFuck.

## Escalation Order

1. curl robots.txt -> chemin vers script JS.
2. Recuperation du script -> contenu entierement en JSFuck.
3. Execution via node script.js -> decodage -> flag en clair.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste (voir lecon ci-dessous).

## Payload Shapes

```text
Reconnaitre la signature JSFuck (uniquement []()!+) et l'executer tel quel sous Node.js/navigateur plutot que de tenter un decodage manuel.
```

## Related Writeups

- clientside-jsfuck-nodejs-decode

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
