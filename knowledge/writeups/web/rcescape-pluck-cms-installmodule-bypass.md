---
doc_kind: writeup
title: "ThunderCipher RCEscape - Pluck CMS 4.7.18, bypass filtre extension via installmodule"
category: web
slug: rcescape-pluck-cms-installmodule-bypass
created: 2026-10-29
status: solved
tags:
  - pluck-cms
  - installmodule-bypass
  - world-readable-ssh-key
  - bash-history-leak
source: thundercipher.in/labs
target: "Pluck CMS 4.7.18"
---
# ThunderCipher RCEscape - Pluck CMS 4.7.18, bypass filtre extension via installmodule

## Challenge Summary

- Source: thundercipher.in/labs
- Target: Pluck CMS 4.7.18
- Goal: Un fichier de deploiement expose un secret d'authentification donnant acces admin a Pluck CMS; les routes classiques filtrent strictement les extensions, mais la route d'installation de module (upload zip) accepte un .php arbitraire.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Fichier de deploiement expose (base64) -> secret.
2. POST login avec ce secret -> acces admin confirme.
3. Routes classiques filtrent .php; la route d'installation de module accepte un .php arbitraire sans filtre.
4. Zip contenant un webshell .php -> upload via installation de module.
5. cmd=id -> RCE confirmee.
6. Lecture d'une cle SSH world-readable -> ssh -> flag user.
7. cat ~/.bash_history -> mot de passe root en clair -> su -> flag root.

## Key Evidence

- Confirmation d'installation reussie du module; bash_history revelant litteralement la commande passwd root en clair.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
Zip contenant un .php webshell uploade via la route d'installation de module; lecture directe de ~/.bash_history.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Sur Pluck CMS, toujours tester la route d'installation de module (upload zip) qui est la seule sans validation d'extension quand les routes classiques sont filtrees; toujours verifier ~/.bash_history de tout compte obtenu.

## Pattern Candidates

- Voir pattern associe de meme slug.
