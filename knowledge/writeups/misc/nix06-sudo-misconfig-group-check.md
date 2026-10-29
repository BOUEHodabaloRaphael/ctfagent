---
doc_kind: writeup
title: "DANTE NIX06 - credentials reutilises puis regle sudo permissive"
category: misc
slug: nix06-sudo-misconfig-group-check
created: 2026-10-29
status: solved
tags:
  - sudo-misconfig
  - credential-harvesting
  - desktop-files
  - lateral-movement
source: "HTB Pro Lab DANTE"
target: "Compte avec regle sudo trop permissive"
---
# DANTE NIX06 - credentials reutilises puis regle sudo permissive

## Challenge Summary

- Source: HTB Pro Lab DANTE
- Target: Compte avec regle sudo trop permissive
- Goal: Acces initial via creds deja obtenus sur une autre machine, puis un second compte (trouve via un fichier Desktop) beneficie d'une regle sudo trop permissive menant directement a root.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Creds deja obtenus -> flag user.
2. Fichier Desktop -> creds d'un autre service exposes.
3. Creds web d'un second compte.
4. sudo -l -> regle permettant sudo -i direct -> root -> flag admin.

## Key Evidence

- sudo -i reussissant sans restriction, acces root confirme.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
sudo -l puis sudo -i (erreur de configuration pure).
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Toujours verifier les fichiers Desktop/documents residuels pour des credentials d'autres comptes, et systematiquement lancer sudo -l sur chaque nouveau compte obtenu.

## Pattern Candidates

- Voir pattern associe de meme slug.
