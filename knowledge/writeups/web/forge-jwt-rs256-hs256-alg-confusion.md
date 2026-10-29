---
doc_kind: writeup
title: "Forge CI/CD (GhostNet CTF) - bypass dev->admin via confusion d'algorithme JWT"
category: web
slug: forge-jwt-rs256-hs256-alg-confusion
created: 2026-10-29
status: solved
tags:
  - jwt
  - alg-confusion
  - jwks
  - rs256-hs256
  - privesc
  - flask
source: "GhostNet CTF Forge (B2R, Hard 300pts)"
target: "App Flask Forge CI/CD, JWKS public"
---
# Forge CI/CD (GhostNet CTF) - bypass dev->admin via confusion d'algorithme JWT

## Challenge Summary

- Source: GhostNet CTF Forge (B2R, Hard 300pts)
- Target: App Flask Forge CI/CD, JWKS public
- Goal: Le verificateur JWT fait confiance au champ alg du token; en renvoyant alg=HS256 et en signant avec le PEM de la cle publique RSA comme secret HMAC, le serveur valide le token car il reutilise le meme PEM pour les deux chemins de verification.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Recon ports -> app Flask derriere nginx.
2. Dump du JS front -> cartographie API.
3. Login avec creds fournies -> JWT RS256.
4. GET /.well-known/jwks.json (non authentifie) -> recupere n/e publics.
5. Reconstruire le PEM public a partir de n/e.
6. Forger un token header alg:HS256, payload role:admin, signer HMAC-SHA256 avec le PEM brut comme cle.
7. Tester sur un endpoint admin -> 200 OK, role admin confirme.

## Key Evidence

- Commentaire source confirme le bug de verification manuelle HS256 avec la cle publique PEM comme secret HMAC; endpoint admin renvoie 200 avec liste complete apres forge du token.

## Dead Ends

- Flag obtenu (role admin confirme), chaine terminee.

## Payloads And Commands

```text
Script Python (cryptography + hmac + base64url) generant un JWT HS256 forge.
```

## Flag / Outcome

- Flag obtenu (role admin confirme), chaine terminee.

## Reusable Lessons

- Chaque fois qu'un JWKS public est expose et que le role/alg n'est pas pinne cote serveur, tester systematiquement l'alg confusion RS256->HS256 en utilisant le PEM public brut comme secret HMAC (inclure le newline final de public_bytes()).

## Pattern Candidates

- Voir pattern associe de meme slug.
