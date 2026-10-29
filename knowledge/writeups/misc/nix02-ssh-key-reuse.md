---
doc_kind: writeup
title: "DANTE NIX02 - reutilisation de cle SSH root pivot"
category: misc
slug: nix02-ssh-key-reuse
created: 2026-10-29
status: solved
tags:
  - ssh-key-reuse
  - pivot
  - credential-reuse
  - lateral-movement
source: "HTB Pro Lab DANTE"
target: "Cle SSH root reutilisee entre machines"
---
# DANTE NIX02 - reutilisation de cle SSH root pivot

## Challenge Summary

- Source: HTB Pro Lab DANTE
- Target: Cle SSH root reutilisee entre machines
- Goal: La cle privee root recuperee sur une machine est reutilisee directement pour un acces root SSH sur une autre, sans exploitation additionnelle.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. ssh -i <cle-dejaobtenue> root@<autre-machine>.
2. Acces root immediat, lecture des flags.

## Key Evidence

- Connexion SSH root reussie sans mot de passe via la cle deja obtenue sur une autre machine.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
ssh -i <cle> root@host.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Toujours retester une cle/credential root valide sur l'ensemble du range interne avant d'investir dans une nouvelle exploitation.

## Pattern Candidates

- Voir pattern associe de meme slug.
