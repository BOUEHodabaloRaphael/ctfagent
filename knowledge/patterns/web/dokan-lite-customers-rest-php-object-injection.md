---
doc_kind: pattern
title: "Correctif partiel: un endpoint REST protege, un autre partageant le meme pipeline oublie"
category: web
slug: dokan-lite-customers-rest-php-object-injection
created: 2026-10-29
status: active
tags:
  - php-object-injection
  - cwe-502
  - wordpress-rest-api
  - incomplete-patch
  - woocommerce-meta
  - gadget-chain
chain_summary: "Quand un plugin corrige la deserialisation non sure sur un endpoint REST (ex: products) mais qu'un autre endpoint (ex: customers) partage la meme fonction d'ecriture de meta-donnees sans etre couvert par le meme guard, l'injection reste possible via le second endpoint."
---
# Correctif partiel: un endpoint REST protege, un autre partageant le meme pipeline oublie

## Chain Summary

- One-line chain: Quand un plugin corrige la deserialisation non sure sur un endpoint REST (ex: products) mais qu'un autre endpoint (ex: customers) partage la meme fonction d'ecriture de meta-donnees sans etre couvert par le meme guard, l'injection reste possible via le second endpoint.
- Typical target shape: Plugin/CMS avec plusieurs endpoints REST ecrivant dans le meme type de stockage (meta_data/usermeta/postmeta) via une fonction commune; un changelog de securite mentionne un correctif sur un endpoint specifique.

## Preconditions

- Plugin/CMS avec plusieurs endpoints REST ecrivant dans le meme type de stockage (meta_data/usermeta/postmeta) via une fonction commune; un changelog de securite mentionne un correctif sur un endpoint specifique.

## Cheap Probes

- Lire le changelog/diff du correctif pour identifier precisement quel endpoint/fonction a ete modifie; chercher d'autres endpoints appelant la meme fonction de stockage sous-jacente sans passer par le meme guard.

## Telltale Evidence

- Un payload malveillant (objet serialise, etc.) refuse sur l'endpoint corrige mais accepte et persiste sur un endpoint voisin partageant le meme pipeline.

## Escalation Order

1. Identifier le endpoint/la fonction corrigee precisement (changelog, diff de version).
2. Chercher les autres endpoints du meme plugin qui ecrivent dans le meme type de donnees (meta_data generique).
3. Tester le payload bloque sur l'endpoint corrige, sur ces endpoints voisins.
4. Confirmer la persistance et la revivification (deserialisation) lors d'une lecture ulterieure.

## Common Mistakes

- S'arreter au premier endpoint corrige sans chercher les endpoints voisins partageant la meme surface de stockage.

## Payload Shapes

```text
PUT /wp-json/dokan/v1/customers/{id} {"meta_data":[{"key":"custom_key","value":"O:6:\"Gadget\":1:{...}"}]}
```

## Related Writeups

- dokan-lite-customers-rest-php-object-injection

## Skill Impact

- Related skill: web-triage (deserialisation): ajouter la verification systematique des endpoints voisins partageant un pipeline de stockage apres un correctif de deserialisation.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
