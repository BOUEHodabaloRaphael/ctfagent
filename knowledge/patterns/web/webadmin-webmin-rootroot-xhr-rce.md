---
doc_kind: pattern
title: "ThunderCipher WebAdmin - Webmin root:root et RCE via module Command Shell (piege XHR)"
category: web
slug: webadmin-webmin-rootroot-xhr-rce
created: 2026-10-29
status: active
tags:
  - webmin-default-creds
  - xhr-header-bypass
  - csrf-protection-trap
  - command-shell-module
chain_summary: "Identifiants par defaut root:root sur Webmin donnent acces au module Command Shell, mais la requete echoue silencieusement sans le header X-Requested-With: XMLHttpRequest."
---
# ThunderCipher WebAdmin - Webmin root:root et RCE via module Command Shell (piege XHR)

## Chain Summary

- One-line chain: Identifiants par defaut root:root sur Webmin donnent acces au module Command Shell, mais la requete echoue silencieusement sans le header X-Requested-With: XMLHttpRequest.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Echec sans header XHR puis succes identique avec header ajoute.

## Escalation Order

1. Login Webmin root:root.
2. Tentative directe sur shell/index.cgi sans header -> echec silencieux.
3. Ajout header X-Requested-With: XMLHttpRequest + referer correct -> execution acceptee.
4. Commande -> flag recupere directement.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste (voir lecon ci-dessous).

## Payload Shapes

```text
Sur Webmin, toujours tester le header X-Requested-With pour tout module qui ne repond rien; si plusieurs modules semblent casses, prioriser le module Command Shell.
```

## Related Writeups

- webadmin-webmin-rootroot-xhr-rce

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
