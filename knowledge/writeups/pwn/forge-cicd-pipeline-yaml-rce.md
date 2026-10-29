---
doc_kind: writeup
title: "Forge CI/CD (GhostNet CTF) - RCE via endpoint Run Pipeline (YAML script non sandboxe)"
category: pwn
slug: forge-cicd-pipeline-yaml-rce
created: 2026-10-29
status: solved
tags:
  - cicd
  - yaml-rce
  - pipeline-abuse
  - b2r
  - container-escape-decoy
source: "GhostNet CTF Forge (B2R, Hard 300pts)"
target: "Endpoint pipelines/run, config YAML"
---
# Forge CI/CD (GhostNet CTF) - RCE via endpoint Run Pipeline (YAML script non sandboxe)

## Challenge Summary

- Source: GhostNet CTF Forge (B2R, Hard 300pts)
- Target: Endpoint pipelines/run, config YAML
- Goal: Une fois admin, l'endpoint de lancement de pipeline accepte une config YAML dont chaque ligne script: est executee comme une vraie commande shell dans le conteneur de la plateforme elle-meme (champ image: purement decoratif, aucune isolation reelle).

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Avec le token admin forge, GET une config de pipeline existante pour voir le schema YAML attendu.
2. POST sur l'endpoint de run avec script: ["id","whoami"] -> confirme execution shell reelle.
3. Remplacer script par une commande d'exfiltration de l'environnement -> flags directement dans les variables d'environnement du process.
4. Flags aussi presents en local sur le filesystem.

## Key Evidence

- Sortie confirmant l'execution shell reelle (uid, groupes incluant docker); variables d'environnement contenant les deux flags (user+root) directement visibles.

## Dead Ends

- Flag user + root obtenus directement via les variables d'environnement du process, chaine terminee (2nd blood sur la plateforme).

## Payloads And Commands

```text
Requete JSON POST contenant un champ config YAML brut avec script: [commande shell arbitraire].
```

## Flag / Outcome

- Flag user + root obtenus directement via les variables d'environnement du process, chaine terminee (2nd blood sur la plateforme).

## Reusable Lessons

- Toute plateforme CI/CD qui execute du YAML utilisateur sans isolation reelle (image: ignore) permet RCE direct via le champ script; toujours tester docker.sock mais verifier qu'il n'est pas un leurre.

## Pattern Candidates

- Voir pattern associe de meme slug.
