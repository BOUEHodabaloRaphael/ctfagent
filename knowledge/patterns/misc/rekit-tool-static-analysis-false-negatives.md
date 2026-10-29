---
doc_kind: pattern
title: "Retour de test REKitV2.py - faux negatifs checksec et fausses alertes crypto"
category: misc
slug: rekit-tool-static-analysis-false-negatives
created: 2026-10-29
status: active
tags:
  - checksec
  - false-negative
  - readelf-sw
  - stripped-binary
  - tool-validation
  - static-analysis
chain_summary: "Sur un lab de verifications compilees avec contenu connu a l'avance, plusieurs echouent: canary non detecte sur binaires strippes faute d'option readelf adaptee, alerte RC4 qui se declenche sur presque tout binaire, Fortify confondu avec un simple canary, entropie par section faussee par un decalage de colonnes."
---
# Retour de test REKitV2.py - faux negatifs checksec et fausses alertes crypto

## Chain Summary

- One-line chain: Sur un lab de verifications compilees avec contenu connu a l'avance, plusieurs echouent: canary non detecte sur binaires strippes faute d'option readelf adaptee, alerte RC4 qui se declenche sur presque tout binaire, Fortify confondu avec un simple canary, entropie par section faussee par un decalage de colonnes.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- readelf -sW montre le symbole du canary sur le binaire stripped alors que REKit repond Canary: Non; alerte RC4 declenchee sur un binaire sans RC4.

## Escalation Order

1. Comparer la sortie de l'outil a une verite etablie par readelf brut sur des binaires compiles avec contenu connu.
2. readelf -sW (symboles versionnes) montre le canary present sur un binaire stripped, alors que l'outil (readelf -s sans -W) le manque.
3. Alerte RC4 de l'outil declenchee sur un binaire quelconque sans aucun RC4 reel -> faux positif heuristique.
4. Verifier chaque heuristique de l'outil contre un cas de controle avant de lui faire confiance en conditions reelles.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste.

## Payload Shapes

```text
Avant de faire confiance au checksec d'un outil de triage maison: verifier qu'il utilise readelf -sW (pas -s) pour resoudre les symboles versionnes sur binaire stripped; verifier que ses heuristiques crypto (motifs d'octets statistiques) ne sont pas de simples faux positifs sans contexte.
```

## Related Writeups

- rekit-tool-static-analysis-false-negatives

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
