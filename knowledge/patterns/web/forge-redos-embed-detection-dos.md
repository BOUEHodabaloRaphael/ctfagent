---
doc_kind: pattern
title: "ReDoS synchrone sur event-loop unique = DoS plateforme entiere"
category: web
slug: forge-redos-embed-detection-dos
created: 2026-10-29
status: active
tags:
  - redos
  - dos
  - regex-backtracking
  - event-loop-blocking
  - single-worker
chain_summary: "Un regex a backtracking quadratique execute synchroneement dans un handler async d'une app mono-worker bloque l'event-loop pour TOUS les utilisateurs, pas seulement l'attaquant, avec un seul message/requete."
---
# ReDoS synchrone sur event-loop unique = DoS plateforme entiere

## Chain Summary

- One-line chain: Un regex a backtracking quadratique execute synchroneement dans un handler async d'une app mono-worker bloque l'event-loop pour TOUS les utilisateurs, pas seulement l'attaquant, avec un seul message/requete.
- Typical target shape: Application ASGI/event-loop unique (Node.js, Python asyncio mono-worker) appliquant un regex utilisateur-controlable (detection de pattern, validation) de maniere synchrone dans le chemin de requete.

## Preconditions

- Application ASGI/event-loop unique (Node.js, Python asyncio mono-worker) appliquant un regex utilisateur-controlable (detection de pattern, validation) de maniere synchrone dans le chemin de requete.

## Cheap Probes

- Mesurer le temps de traitement d'une entree avec un motif repete en fonction de la taille (doubler la taille et observer si le temps double ou quadruple).

## Telltale Evidence

- Croissance quadratique (ou pire) du temps de traitement avec la taille de l'entree, visible meme offline sur le regex isole.

## Escalation Order

1. Identifier un regex applique sur une entree utilisateur-controlable (texte libre, URL, nom de fichier).
2. Tester offline la complexite du regex avec des entrees de taille croissante contenant un motif adversarial repete.
3. Si quadratique/exponentiel, construire un payload a la taille maximale autorisee par l'application.
4. Envoyer ce payload et mesurer l'impact sur une requete non liee d'un autre compte pendant le traitement.

## Common Mistakes

- Executer un regex potentiellement couteux de maniere synchrone dans un handler async sans offload (worker thread/process pool) sur une app mono-worker.

## Payload Shapes

```text
('<motif declencheur>' * N)[:max_len]  comme contenu de message/texte libre
```

## Related Writeups

- forge-redos-embed-detection-dos

## Skill Impact

- Related skill: web-triage (DoS): ajouter l'analyse de complexite regex (ReDoS) comme test systematique sur tout champ texte libre d'une app mono-worker.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
