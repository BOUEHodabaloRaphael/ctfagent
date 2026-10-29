---
doc_kind: writeup
title: "Ecriture libre dans .git/ -> execution de commande root via filtre git"
category: web
slug: forge-git-filter-rce
created: 2026-10-29
status: solved
tags:
  - rce
  - git-filter
  - root-container-compromise
  - arbitrary-write
source: "Programme de divulgation reelle Forge/RodiumAI"
target: "Plateforme Forge (RodiumAI) - API multi-tenant"
---
# Ecriture libre dans .git/ -> execution de commande root via filtre git

## Challenge Summary

- Source: Programme de divulgation reelle Forge/RodiumAI
- Target: Plateforme Forge (RodiumAI) - API multi-tenant
- Goal: L'API d'edition de fichiers ne protege pas .git/ en ecriture; un utilisateur peut ecrire un .git/config malveillant definissant un filtre clean qui execute une commande shell au prochain git add -A systeme.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source report)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Constater que delete_file/rename_path bloquent .git mais pas write_file/write_bytes.
2. PUT .git/config avec un filter clean = commande shell arbitraire.
3. PUT .gitattributes mappant un fichier trigger sur ce filtre.
4. PUT du fichier trigger (non suivi).
5. Toute sauvegarde suivante declenche history.snapshot() -> git add -A -> le filtre s'execute en root dans le conteneur.
6. Lire le resultat via GET sur un fichier public de sortie de commande.

## Key Evidence

- Lecture via l'API renvoyant "uid=0(root) gid=0(root) groups=0(root)" apres les PUT et un save declenchant git add -A.

## Dead Ends

- n/a - chaine confirmee de bout en bout.

## Payloads And Commands

```text
4 requetes HTTP PUT JSON (.git/config, .gitattributes, trigger.txt, trigger2.txt) + 1 GET de lecture.
```

## Flag / Outcome

- Vulnerabilite confirmee et reportee.

## Reusable Lessons

- Un repo git interne utilise comme feature produit expose via la meme API de fichiers que l'arbre utilisateur: bloquer l'ecriture (pas seulement suppression/renommage) sur .git, sinon filtre/hook git = RCE par design. Point d'escalade ultime du programme: rend obsoletes les autres bugs d'autorisation une fois atteint (lecture de secrets -> forge de session admin).

## Pattern Candidates

- Nouveau pattern: git-filter-attribute-rce-via-file-api
