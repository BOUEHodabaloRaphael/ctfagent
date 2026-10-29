---
doc_kind: writeup
title: "Race TOCTOU entre renommage de slug et publish concurrent d'un tenant tiers"
category: web
slug: forge-slug-rename-purge-race-cross-tenant-wipe
created: 2026-10-29
status: solved
tags:
  - race-condition
  - toctou
  - slug-rename
  - object-storage
  - cross-tenant
source: "Programme de divulgation reelle Forge/RodiumAI"
target: "Plateforme Forge (RodiumAI) - API multi-tenant"
---
# Race TOCTOU entre renommage de slug et publish concurrent d'un tenant tiers

## Challenge Summary

- Source: Programme de divulgation reelle Forge/RodiumAI
- Target: Plateforme Forge (RodiumAI) - API multi-tenant
- Goal: La contrainte unique de slug est liberee en DB avant la fin du nettoyage asynchrone de l'object store; un second tenant peut reclamer et publier sur ce slug pendant la fenetre, et le nettoyage tardif du premier proprietaire supprime alors le contenu du nouveau.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source report)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Compte A publie un gros site (padding massif) puis renomme son projet (libere le slug en DB avant le nettoyage de l'objet store).
2. Compte B (sans lien avec A) boucle sur un rename jusqu'a reclamer le meme slug puis publie immediatement.
3. Les deux operations s'executent en concurrence: le nettoyage de A supprime tout ce qui est sous le prefixe au moment ou il s'execute, sans distinguer anciens et nouveaux objets.
4. Plus le padding de A est grand, plus la fenetre est large et deterministe.
5. Verification: site de B devient inaccessible; confirmation directe que le prefixe objet est vide.

## Key Evidence

- Table padding/duree-purge/duree-claim-publish montrant une collision deterministe a un seuil mesure; confirmation par listing direct du bucket objet apres un publish qui avait pourtant renvoye succes.

## Dead Ends

- n/a - collision rendue deterministe par le controle de la taille du padding par l'attaquant lui-meme.

## Payloads And Commands

```text
Deux comptes + scripts HTTP concurrents (threads): boucle PATCH slug + POST publish synchronises contre un rename sur un projet charge de milliers de fichiers factices.
```

## Flag / Outcome

- Vulnerabilite confirmee et reportee.

## Reusable Lessons

- Liberation d'une ressource unique en DB avant fin du nettoyage asynchrone cross-systeme (TOCTOU multi-store): toute feature de renommage liberant une contrainte d'unicite avant nettoyage physique garanti cree une fenetre de course amplifiable par l'attaquant lui-meme. Meme composant que forge-slug-stale-files-inherited-by-new-tenant: squatter des slugs generiques a l'avance puis declencher la variante race au bon moment pour effacer activement le contenu d'une vraie cible.

## Pattern Candidates

- Nouveau pattern: db-unique-release-before-async-cleanup-race
