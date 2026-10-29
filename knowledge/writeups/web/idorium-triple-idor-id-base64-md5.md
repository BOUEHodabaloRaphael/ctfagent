---
doc_kind: writeup
title: "ThunderCipher IDORium - triple IDOR (ID direct, base64, MD5 du user_id)"
category: web
slug: idorium-triple-idor-id-base64-md5
created: 2026-10-29
status: solved
tags:
  - idor
  - base64-id-obfuscation
  - md5-filename-guessing
  - broken-access-control
source: thundercipher.in/labs
target: "Application avec controles d'acces absents sur 3 variantes d'ID"
---
# ThunderCipher IDORium - triple IDOR (ID direct, base64, MD5 du user_id)

## Challenge Summary

- Source: thundercipher.in/labs
- Target: Application avec controles d'acces absents sur 3 variantes d'ID
- Goal: Trois sous-flags via trois variantes d'IDOR: acces direct par ID numerique, acces via un ID encode en base64, et acces via un nom de fichier = MD5(user_id).

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. GET /view_profile/0 (session guest) -> acces profil admin.
2. GET /product/<base64(id)> -> produit cache.
3. Pistes echouees avant: SSTI, SQLi, IDOR session-scoped.
4. hashlib.md5(user_id) -> nom de fichier.
5. GET /static/images/<md5(user_id)>.png -> image d'un autre utilisateur.

## Key Evidence

- Trois reponses flag distinctes confirmant l'absence de controle d'acces sur ID numerique, ID base64 et nom de fichier derive par hash previsible.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
Manipulation directe d'ID dans l'URL; encodage base64 d'un ID candidat; calcul MD5(user_id) pour deviner un nom de fichier.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Toujours tester l'IDOR sous ses trois formes (ID brut, ID encode/obscurci, ID transforme par hash previsible dans un nom de ressource statique).

## Pattern Candidates

- Voir pattern associe de meme slug.
