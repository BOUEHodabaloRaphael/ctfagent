---
doc_kind: pattern
title: "Contenu publie residuel herite par un nouveau tenant sur un slug reutilise"
category: web
slug: forge-slug-stale-files-inherited-by-new-tenant
created: 2026-10-29
status: active
tags:
  - incomplete-cleanup
  - slug-reuse
  - stale-content
  - phishing-planting
  - object-storage
chain_summary: "Un systeme de publication par prefixe partage qui ne purge jamais le prefixe au renommage/republish (seule la suppression totale du projet nettoie) laisse du contenu residuel permanent, heritable par n'importe quel tiers reclamant le meme nom plus tard."
---
# Contenu publie residuel herite par un nouveau tenant sur un slug reutilise

## Chain Summary

- One-line chain: Un systeme de publication par prefixe partage qui ne purge jamais le prefixe au renommage/republish (seule la suppression totale du projet nettoie) laisse du contenu residuel permanent, heritable par n'importe quel tiers reclamant le meme nom plus tard.
- Typical target shape: Plateforme de publication de sites/contenus statiques par slug/prefixe reutilisable, avec un stockage objet append-only (publish n'ecrase que ses propres fichiers, ne diff jamais avec l'etat precedent).

## Preconditions

- Plateforme de publication de sites/contenus statiques par slug/prefixe reutilisable, avec un stockage objet append-only (publish n'ecrase que ses propres fichiers, ne diff jamais avec l'etat precedent).

## Cheap Probes

- Publier un fichier marqueur sur un slug, renommer le projet, puis verifier si ce fichier marqueur reste accessible publiquement malgre l'absence de projet associe au slug.

## Telltale Evidence

- Le fichier marqueur reste accessible (code succes + contenu original) apres le renommage, et persiste meme apres qu'un autre projet publie sur le meme slug.

## Escalation Order

1. Identifier une plateforme avec slugs/prefixes de publication reutilisables.
2. Publier un contenu marqueur/malveillant sur un slug libre anticipant un futur usage.
3. Renommer ou liberer le projet d'origine sans suppression complete.
4. Attendre ou provoquer la reclamation du meme slug par un autre tenant.
5. Verifier l'accessibilite du contenu residuel original aux cotes du nouveau contenu.

## Common Mistakes

- Implementer le publish comme un simple upload additif sans jamais diff/purge du prefixe par rapport a l'etat precedent, en ne nettoyant qu'a la suppression totale du projet.

## Payload Shapes

```text
PUT /sites/{slug}/malicious.html puis PATCH /projects/{id}/rename puis attendre reclamation tierce
```

## Related Writeups

- forge-slug-stale-files-inherited-by-new-tenant, forge-slug-rename-purge-race-cross-tenant-wipe, forge-domain-takeover-dangling-cname

## Skill Impact

- Related skill: web-triage (cleanup/multi-tenant): ajouter le test de persistance de contenu residuel apres renommage/liberation de slug comme sous-cas de stale-content sur toute plateforme de publication partagee.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
