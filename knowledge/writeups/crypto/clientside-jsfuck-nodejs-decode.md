---
doc_kind: writeup
title: "ThunderCipher Client Side - script JSFuck execute en Node.js pour reveler le flag"
category: crypto
slug: clientside-jsfuck-nodejs-decode
created: 2026-10-29
status: solved
tags:
  - jsfuck
  - js-obfuscation
  - nodejs-execution
  - client-side-secret
source: thundercipher.in/labs
target: "Script JS obfusque en JSFuck"
---
# ThunderCipher Client Side - script JSFuck execute en Node.js pour reveler le flag

## Challenge Summary

- Source: thundercipher.in/labs
- Target: Script JS obfusque en JSFuck
- Goal: robots.txt pointe vers un script JS obfusque en JSFuck (uniquement les caracteres []()!+); son execution directe sous Node.js revele le flag en clair.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. curl robots.txt -> chemin vers script JS.
2. Recuperation du script -> contenu entierement en JSFuck.
3. Execution via node script.js -> decodage -> flag en clair.

## Key Evidence

- Sortie console Node.js affichant directement le flag apres execution du blob JSFuck.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
Execution directe node <fichier.js> du blob JSFuck recupere.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Reconnaitre la signature JSFuck (uniquement []()!+) et l'executer tel quel sous Node.js/navigateur plutot que de tenter un decodage manuel.

## Pattern Candidates

- Voir pattern associe de meme slug.
