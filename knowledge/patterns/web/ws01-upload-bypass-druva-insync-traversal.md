---
doc_kind: pattern
title: "DANTE WS01 - bypass filtre upload forum et Druva InSync path traversal (EDB-48505)"
category: web
slug: ws01-upload-bypass-druva-insync-traversal
created: 2026-10-29
status: active
tags:
  - upload-bypass
  - double-extension
  - path-traversal
  - edb-48505
  - forum-avatar
chain_summary: "Un forum filtre l'upload d'avatar sur l'extension seule (contournable par double extension/magic bytes); Druva InSync 6.6.3 est vulnerable a une traversee de chemin distante (EDB-48505)."
---
# DANTE WS01 - bypass filtre upload forum et Druva InSync path traversal (EDB-48505)

## Chain Summary

- One-line chain: Un forum filtre l'upload d'avatar sur l'extension seule (contournable par double extension/magic bytes); Druva InSync 6.6.3 est vulnerable a une traversee de chemin distante (EDB-48505).

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Execution confirmee du payload PHP malgre filtre; exploit public deposant une webshell fonctionnelle.

## Escalation Order

1. gobuster dir -> forum decouvert.
2. Upload avatar avec double extension ou magic bytes image + payload PHP -> webshell execute malgre filtre.
3. Exploitation Druva InSync 6.6.3 (script exploit public) -> traversee de chemin -> upload distant -> RCE.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste (voir lecon ci-dessous).

## Payload Shapes

```text
Filtre d'upload base extension seule (sans verif MIME/contenu) contournable par double extension/magic bytes; verifier systematiquement les CVE EDB publiques pour toute version logicielle identifiee.
```

## Related Writeups

- ws01-upload-bypass-druva-insync-traversal

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
