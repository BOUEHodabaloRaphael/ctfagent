---
doc_kind: writeup
title: "DANTE WS01 - bypass filtre upload forum et Druva InSync path traversal (EDB-48505)"
category: web
slug: ws01-upload-bypass-druva-insync-traversal
created: 2026-10-29
status: solved
tags:
  - upload-bypass
  - double-extension
  - path-traversal
  - edb-48505
  - forum-avatar
source: "HTB Pro Lab DANTE"
target: "Forum (upload avatar) + Druva InSync 6.6.3"
---
# DANTE WS01 - bypass filtre upload forum et Druva InSync path traversal (EDB-48505)

## Challenge Summary

- Source: HTB Pro Lab DANTE
- Target: Forum (upload avatar) + Druva InSync 6.6.3
- Goal: Un forum filtre l'upload d'avatar sur l'extension seule (contournable par double extension/magic bytes); Druva InSync 6.6.3 est vulnerable a une traversee de chemin distante (EDB-48505).

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. gobuster dir -> forum decouvert.
2. Upload avatar avec double extension ou magic bytes image + payload PHP -> webshell execute malgre filtre.
3. Exploitation Druva InSync 6.6.3 (script exploit public) -> traversee de chemin -> upload distant -> RCE.

## Key Evidence

- Execution confirmee du payload PHP malgre filtre; exploit public deposant une webshell fonctionnelle.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
Fichier upload double-extension/magic-bytes; script exploit public EDB-ID 48505.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Filtre d'upload base extension seule (sans verif MIME/contenu) contournable par double extension/magic bytes; verifier systematiquement les CVE EDB publiques pour toute version logicielle identifiee.

## Pattern Candidates

- Voir pattern associe de meme slug.
