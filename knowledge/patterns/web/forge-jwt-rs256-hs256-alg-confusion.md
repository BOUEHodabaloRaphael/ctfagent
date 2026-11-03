---
doc_kind: pattern
title: "Forge CI/CD (GhostNet CTF) - bypass dev->admin via confusion d'algorithme JWT"
category: web
slug: forge-jwt-rs256-hs256-alg-confusion
created: 2026-10-29
status: active
tags:
  - jwt
  - alg-confusion
  - jwks
  - rs256-hs256
  - privesc
  - flask
chain_summary: "Le verificateur JWT fait confiance au champ alg du token; en renvoyant alg=HS256 et en signant avec le PEM de la cle publique RSA comme secret HMAC, le serveur valide le token car il reutilise le meme PEM pour les deux chemins de verification."
---
# Forge CI/CD (GhostNet CTF) - bypass dev->admin via confusion d'algorithme JWT

## Chain Summary

- One-line chain: Le verificateur JWT fait confiance au champ alg du token; en renvoyant alg=HS256 et en signant avec le PEM de la cle publique RSA comme secret HMAC, le serveur valide le token car il reutilise le meme PEM pour les deux chemins de verification.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Commentaire source confirme le bug de verification manuelle HS256 avec la cle publique PEM comme secret HMAC; endpoint admin renvoie 200 avec liste complete apres forge du token.

## Escalation Order

1. Recon ports -> app Flask derriere nginx.
2. Dump du JS front -> cartographie API.
3. Login avec creds fournies -> JWT RS256.
4. GET /.well-known/jwks.json (non authentifie) -> recupere n/e publics.
5. Reconstruire le PEM public a partir de n/e.
6. Forger un token header alg:HS256, payload role:admin, signer HMAC-SHA256 avec le PEM brut comme cle.
7. Tester sur un endpoint admin -> 200 OK, role admin confirme.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste.

## Payload Shapes

```text
Chaque fois qu'un JWKS public est expose et que le role/alg n'est pas pinne cote serveur, tester systematiquement l'alg confusion RS256->HS256 en utilisant le PEM public brut comme secret HMAC (inclure le newline final de public_bytes()).
```

## Related Writeups

- forge-jwt-rs256-hs256-alg-confusion
- [AFRICC 2027 Qualifiers — full writeup](../../writeups/misc/africc2027-quals-full-writeup.md) — "Confused Deputy" (100pts, Web), a second independent confirmation of the exact same technique (public key from `/jwks.json`, forged `role=admin` HS256 token).

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
