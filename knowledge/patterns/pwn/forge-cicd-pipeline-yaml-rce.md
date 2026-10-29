---
doc_kind: pattern
title: "Forge CI/CD (GhostNet CTF) - RCE via endpoint Run Pipeline (YAML script non sandboxe)"
category: pwn
slug: forge-cicd-pipeline-yaml-rce
created: 2026-10-29
status: active
tags:
  - cicd
  - yaml-rce
  - pipeline-abuse
  - b2r
  - container-escape-decoy
chain_summary: "Une fois admin, l'endpoint de lancement de pipeline accepte une config YAML dont chaque ligne script: est executee comme une vraie commande shell dans le conteneur de la plateforme elle-meme (champ image: purement decoratif, aucune isolation reelle)."
---
# Forge CI/CD (GhostNet CTF) - RCE via endpoint Run Pipeline (YAML script non sandboxe)

## Chain Summary

- One-line chain: Une fois admin, l'endpoint de lancement de pipeline accepte une config YAML dont chaque ligne script: est executee comme une vraie commande shell dans le conteneur de la plateforme elle-meme (champ image: purement decoratif, aucune isolation reelle).

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Sortie confirmant l'execution shell reelle (uid, groupes incluant docker); variables d'environnement contenant les deux flags (user+root) directement visibles.

## Escalation Order

1. Avec le token admin forge, GET une config de pipeline existante pour voir le schema YAML attendu.
2. POST sur l'endpoint de run avec script: ["id","whoami"] -> confirme execution shell reelle.
3. Remplacer script par une commande d'exfiltration de l'environnement -> flags directement dans les variables d'environnement du process.
4. Flags aussi presents en local sur le filesystem.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste.

## Payload Shapes

```text
Toute plateforme CI/CD qui execute du YAML utilisateur sans isolation reelle (image: ignore) permet RCE direct via le champ script; toujours tester docker.sock mais verifier qu'il n'est pas un leurre.
```

## Related Writeups

- forge-cicd-pipeline-yaml-rce

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
