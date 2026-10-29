---
doc_kind: pattern
title: "ThunderCipher Trust Me Not - Monitorr 1.7.6m RCE non authentifiee via upload.php"
category: web
slug: trustmenot-monitorr-magicbytes-rce
created: 2026-10-29
status: active
tags:
  - monitorr
  - magic-bytes-bypass
  - unauth-upload-rce
  - world-readable-flag
chain_summary: "Monitorr 1.7.6m contient une RCE connue non authentifiee dans upload.php: un fichier PHP prefixe des magic bytes GIF89a passe le filtre et est stocke executable."
---
# ThunderCipher Trust Me Not - Monitorr 1.7.6m RCE non authentifiee via upload.php

## Chain Summary

- One-line chain: Monitorr 1.7.6m contient une RCE connue non authentifiee dans upload.php: un fichier PHP prefixe des magic bytes GIF89a passe le filtre et est stocke executable.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Reponse confirmant l'upload puis uid=33(www-data) sur ?cmd=id.

## Escalation Order

1. Identification version via commentaire HTML -> Monitorr 1.7.6m, RCE connue.
2. Fichier GIF89a + PHP system($_GET['cmd']) -> POST multipart vers upload.php avec header X-Requested-With.
3. Fichier stocke et execution confirmee (id).
4. Flags world-readable -> cat direct sans privesc.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste (voir lecon ci-dessous).

## Payload Shapes

```text
Monitorr upload.php necessite le header X-Requested-With pour accepter l'upload; magic bytes GIF89a en prefixe suffit a bypasser le filtre image.
```

## Related Writeups

- trustmenot-monitorr-magicbytes-rce

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
