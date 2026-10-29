---
doc_kind: pattern
title: "ThunderCipher RCEscape - Pluck CMS 4.7.18, bypass filtre extension via installmodule"
category: web
slug: rcescape-pluck-cms-installmodule-bypass
created: 2026-10-29
status: active
tags:
  - pluck-cms
  - installmodule-bypass
  - world-readable-ssh-key
  - bash-history-leak
chain_summary: "Un fichier de deploiement expose un secret d'authentification donnant acces admin a Pluck CMS; les routes classiques filtrent strictement les extensions, mais la route d'installation de module (upload zip) accepte un .php arbitraire."
---
# ThunderCipher RCEscape - Pluck CMS 4.7.18, bypass filtre extension via installmodule

## Chain Summary

- One-line chain: Un fichier de deploiement expose un secret d'authentification donnant acces admin a Pluck CMS; les routes classiques filtrent strictement les extensions, mais la route d'installation de module (upload zip) accepte un .php arbitraire.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Confirmation d'installation reussie du module; bash_history revelant litteralement la commande passwd root en clair.

## Escalation Order

1. Fichier de deploiement expose (base64) -> secret.
2. POST login avec ce secret -> acces admin confirme.
3. Routes classiques filtrent .php; la route d'installation de module accepte un .php arbitraire sans filtre.
4. Zip contenant un webshell .php -> upload via installation de module.
5. cmd=id -> RCE confirmee.
6. Lecture d'une cle SSH world-readable -> ssh -> flag user.
7. cat ~/.bash_history -> mot de passe root en clair -> su -> flag root.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste (voir lecon ci-dessous).

## Payload Shapes

```text
Sur Pluck CMS, toujours tester la route d'installation de module (upload zip) qui est la seule sans validation d'extension quand les routes classiques sont filtrees; toujours verifier ~/.bash_history de tout compte obtenu.
```

## Related Writeups

- rcescape-pluck-cms-installmodule-bypass

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
