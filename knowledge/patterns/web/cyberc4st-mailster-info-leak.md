---
doc_kind: pattern
title: "WordPress REST: CPT generique wp/v2 non protege alors que l'API custom du plugin l'est"
category: web
slug: cyberc4st-mailster-info-leak
created: 2026-10-29
status: active
tags:
  - web
  - wordpress
  - information-disclosure
  - rest-api-misconfig
  - stack-trace-leak
  - bug-bounty-reel
chain_summary: "Un plugin WordPress protege correctement son API REST custom (v1/*) mais oublie souvent de proteger le Custom Post Type generique expose automatiquement via wp/v2/{cpt}."
---
# WordPress REST: CPT generique wp/v2 non protege alors que l'API custom du plugin l'est

## Chain Summary

- One-line chain: Un plugin WordPress protege correctement son API REST custom (v1/*) mais oublie souvent de proteger le Custom Post Type generique expose automatiquement via wp/v2/{cpt}.
- Typical target shape: Plugin WordPress enregistrant un Custom Post Type (formulaire, config, etc.) ET exposant une API REST custom protegee pour le meme type de donnees.

## Preconditions

- Plugin WordPress enregistrant un Custom Post Type (formulaire, config, etc.) ET exposant une API REST custom protegee pour le meme type de donnees.

## Cheap Probes

- Enumerer wp-json/ (index) pour lister toutes les routes enregistrees; tester wp/v2/{nom-du-cpt-du-plugin}/{id} en parallele de l'API custom plugin/v1/*.

## Telltale Evidence

- Route wp/v2/{cpt} repond 200 sans auth alors que la route custom equivalente du plugin repond 401/403.

## Escalation Order

1. Identifier le(s) Custom Post Type(s) enregistres par le plugin cible (souvent visible dans wp-json/ index ou le code source du plugin).
2. Tester l'API custom du plugin (v1/* generalement protegee) ET la route generique wp/v2/{cpt} pour le meme objet.
3. Si wp/v2/{cpt} repond sans auth, extraire les champs exposes (souvent configuration complete, parfois sensible).

## Common Mistakes

- S'arreter a 401 sur l'API custom du plugin sans tester la route REST generique wp/v2 pour le meme type d'objet.

## Payload Shapes

```text
GET /wp-json/wp/v2/{cpt-slug}/{id}  (sans aucune authentification)
```

## Related Writeups

- cyberc4st-mailster-info-leak

## Skill Impact

- Related skill: web-triage (WordPress): ajouter le test systematique wp/v2/{cpt} en parallele de toute API REST custom de plugin protegee.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
