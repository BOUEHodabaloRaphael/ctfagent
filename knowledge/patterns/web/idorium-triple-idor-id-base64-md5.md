---
doc_kind: pattern
title: "ThunderCipher IDORium - triple IDOR (ID direct, base64, MD5 du user_id)"
category: web
slug: idorium-triple-idor-id-base64-md5
created: 2026-10-29
status: active
tags:
  - idor
  - base64-id-obfuscation
  - md5-filename-guessing
  - broken-access-control
chain_summary: "Trois sous-flags via trois variantes d'IDOR: acces direct par ID numerique, acces via un ID encode en base64, et acces via un nom de fichier = MD5(user_id)."
---
# ThunderCipher IDORium - triple IDOR (ID direct, base64, MD5 du user_id)

## Chain Summary

- One-line chain: Trois sous-flags via trois variantes d'IDOR: acces direct par ID numerique, acces via un ID encode en base64, et acces via un nom de fichier = MD5(user_id).

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Trois reponses flag distinctes confirmant l'absence de controle d'acces sur ID numerique, ID base64 et nom de fichier derive par hash previsible.

## Escalation Order

1. GET /view_profile/0 (session guest) -> acces profil admin.
2. GET /product/<base64(id)> -> produit cache.
3. Pistes echouees avant: SSTI, SQLi, IDOR session-scoped.
4. hashlib.md5(user_id) -> nom de fichier.
5. GET /static/images/<md5(user_id)>.png -> image d'un autre utilisateur.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste (voir lecon ci-dessous).

## Payload Shapes

```text
Toujours tester l'IDOR sous ses trois formes (ID brut, ID encode/obscurci, ID transforme par hash previsible dans un nom de ressource statique).
```

## Related Writeups

- idorium-triple-idor-id-base64-md5

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
