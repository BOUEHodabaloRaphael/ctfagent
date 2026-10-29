---
doc_kind: pattern
title: "Fuite .DS_Store exposant l'arborescence complete d'un site"
category: web
slug: poo-recon-dsstore-leak
created: 2026-10-29
status: active
tags:
  - dsstore-leak
  - iis
  - info-disclosure
  - path-enumeration
  - web-config
chain_summary: "Un fichier .DS_Store accessible (200) sur un serveur web expose, une fois parse, la liste complete des fichiers/dossiers du repertoire, y compris des noms non lies autrement."
---
# Fuite .DS_Store exposant l'arborescence complete d'un site

## Chain Summary

- One-line chain: Un fichier .DS_Store accessible (200) sur un serveur web expose, une fois parse, la liste complete des fichiers/dossiers du repertoire, y compris des noms non lies autrement.
- Typical target shape: Serveur web (IIS, Apache, nginx statique) ou un developpeur macOS a deploye son dossier local sans exclure .DS_Store.

## Preconditions

- Serveur web (IIS, Apache, nginx statique) ou un developpeur macOS a deploye son dossier local sans exclure .DS_Store.

## Cheap Probes

- curl -I <site>/.DS_Store et dans chaque sous-dossier decouvert.

## Telltale Evidence

- Reponse 200 avec un fichier binaire de quelques Ko.

## Escalation Order

1. Tester .DS_Store a la racine et dans chaque sous-dossier decouvert.
2. Parser le format binaire (ou utiliser un outil dedie) pour extraire les noms de fichiers/dossiers.
3. Suivre les nouveaux chemins decouverts recursivement.
4. Chercher des fichiers de config/connexion dans les dossiers reveles.

## Common Mistakes

- S'arreter a la racine sans tester .DS_Store dans chaque sous-dossier decouvert.

## Payload Shapes

```text
curl -s <site>/.DS_Store -o ds_store.bin puis parsing Python du format proprietaire
```

## Related Writeups

- poo-recon-dsstore-leak

## Skill Impact

- Related skill: web-triage: ajouter le test systematique .DS_Store (racine + sous-dossiers) comme sonde de recon passive peu couteuse.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
