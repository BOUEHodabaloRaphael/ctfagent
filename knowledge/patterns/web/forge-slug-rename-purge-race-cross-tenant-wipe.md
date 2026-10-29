---
doc_kind: pattern
title: "Race TOCTOU: liberation DB d'une ressource unique avant nettoyage asynchrone cross-store"
category: web
slug: forge-slug-rename-purge-race-cross-tenant-wipe
created: 2026-10-29
status: active
tags:
  - race-condition
  - toctou
  - slug-rename
  - object-storage
  - cross-tenant
chain_summary: "Quand un renommage libere une contrainte unique en base avant que le nettoyage physique associe (object store) soit garanti termine, un tiers peut reclamer la ressource et subir un nettoyage tardif qui efface son propre contenu."
---
# Race TOCTOU: liberation DB d'une ressource unique avant nettoyage asynchrone cross-store

## Chain Summary

- One-line chain: Quand un renommage libere une contrainte unique en base avant que le nettoyage physique associe (object store) soit garanti termine, un tiers peut reclamer la ressource et subir un nettoyage tardif qui efface son propre contenu.
- Typical target shape: Systeme avec une ressource nommee unique (slug, nom de fichier, identifiant) stockee en DB et associee a un stockage physique externe (object store) nettoye de maniere asynchrone au renommage/suppression.

## Preconditions

- Systeme avec une ressource nommee unique (slug, nom de fichier, identifiant) stockee en DB et associee a un stockage physique externe (object store) nettoye de maniere asynchrone au renommage/suppression.

## Cheap Probes

- Renommer une ressource chargee avec un gros volume de donnees a nettoyer, puis chronometrer combien de temps avant que le nettoyage physique soit effectivement termine vs la liberation DB immediate du nom.

## Telltale Evidence

- Le nom redevient immediatement disponible en DB alors que le nettoyage physique associe prend un temps mesurable proportionnel au volume de donnees.

## Escalation Order

1. Identifier une ressource nommee unique dont le renommage libere immediatement la contrainte DB.
2. Charger la ressource d'origine avec un volume important pour maximiser la duree du nettoyage physique associe.
3. Renommer la ressource d'origine pour liberer le nom.
4. En parallele (autre compte), reclamer le nom libere et y publier/ecrire immediatement.
5. Verifier si le nettoyage tardif de l'operation d'origine supprime le nouveau contenu du tiers.

## Common Mistakes

- Liberer une contrainte d'unicite en base avant que le nettoyage physique associe soit garanti atomique/termine (ou avant d'utiliser un identifiant de version/generation pour distinguer ancien et nouveau contenu sous le meme nom).

## Payload Shapes

```text
Thread A: rename(gros_projet) ; Thread B (boucle): try_claim_slug(meme_nom) puis publish()
```

## Related Writeups

- forge-slug-rename-purge-race-cross-tenant-wipe, forge-slug-stale-files-inherited-by-new-tenant

## Skill Impact

- Related skill: web-triage (race condition): ajouter le pattern 'renommage + nettoyage asynchrone cross-store' comme sous-cas de race condition multi-tenant a fort impact.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
