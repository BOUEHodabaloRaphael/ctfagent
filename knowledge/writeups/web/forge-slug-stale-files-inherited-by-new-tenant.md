---
doc_kind: writeup
title: "Fichiers publies residuels survivent au renommage de slug"
category: web
slug: forge-slug-stale-files-inherited-by-new-tenant
created: 2026-10-29
status: solved
tags:
  - incomplete-cleanup
  - slug-reuse
  - stale-content
  - phishing-planting
  - object-storage
source: "Programme de divulgation reelle Forge/RodiumAI"
target: "Plateforme Forge (RodiumAI) - API multi-tenant"
---
# Fichiers publies residuels survivent au renommage de slug

## Challenge Summary

- Source: Programme de divulgation reelle Forge/RodiumAI
- Target: Plateforme Forge (RodiumAI) - API multi-tenant
- Goal: Le publish ne nettoie jamais le prefixe de stockage au renommage ni au republish normal; un attaquant squatte un slug, y plante du contenu, le libere, et ce contenu reste servi meme apres qu'un tiers legitime reclame le meme slug.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source report)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Attaquant publie des fichiers malveillants sur un slug anticipe comme futur nom d'une cible.
2. Attaquant renomme son projet - aucune suppression des fichiers sous l'ancien prefixe (stockage append-only).
3. Les fichiers plantes restent servis publiquement meme sans projet associe.
4. Victime reclame le meme slug libre et publie son propre site -> publish ajoute/ecrase seulement ses propres fichiers sans purger le reste.
5. Resultat: index de la victime normal, mais fichiers de l'attaquant toujours accessibles sur le meme prefixe.
6. Variante mono-tenant: un fichier sensible supprime localement puis republie reste quand meme servi pour toujours.

## Key Evidence

- Sequence de requetes confirmant que le fichier plante par l'attaquant renvoie toujours succes avec le contenu original APRES que la victime ait publie son site legitime sur le meme slug.

## Dead Ends

- n/a - deterministe, pas de race necessaire.

## Payloads And Commands

```text
Sequence HTTP deterministe: publish attaquant -> rename -> claim victime -> publish victime -> GET de verification.
```

## Flag / Outcome

- Vulnerabilite confirmee et reportee.

## Reusable Lessons

- Stockage objet append-only sans purge au renommage/republish, seule la suppression totale du projet nettoie: tout systeme de publication par prefixe partage doit purger (diff) a CHAQUE publish/renommage, sinon le contenu residuel est permanent et heritable par un tiers.

## Pattern Candidates

- Nouveau pattern: append-only-publish-stale-content-inheritance
