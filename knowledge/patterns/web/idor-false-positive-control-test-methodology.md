---
doc_kind: pattern
title: "IDOR: test de controle obligatoire avant de conclure a une faille (eviter le faux positif)"
category: web
slug: idor-false-positive-control-test-methodology
created: 2026-10-30
status: active
tags:
  - legacy-memory-migration
  - nctf26-prep
  - idor
chain_summary: "Un endpoint qui accepte des parametres d'un autre compte et renvoie 'not_found' au lieu d'une erreur d'autorisation n'est pas forcement un IDOR — il peut simplement ignorer totalement ces parametres et ne regarder que la session active, ce qui produit exactement la meme reponse."
---
# IDOR: test de controle obligatoire avant de conclure a une faille (eviter le faux positif)

## Chain Summary

- One-line chain: Un endpoint qui accepte des parametres d'un autre compte et renvoie 'not_found' au lieu d'une erreur d'autorisation n'est pas forcement un IDOR — il peut simplement ignorer totalement ces parametres et ne regarder que la session active, ce qui produit exactement la meme reponse.

## Preconditions

- Endpoint parametre (query string, body JSON) soupconne d'IDOR, ou l'on pense que les parametres sont verifies contre la session active.

## Cheap Probes

- Depuis SA PROPRE session authentifiee, interroger l'endpoint avec des parametres VOLONTAIREMENT FAUX/differents des siens (mauvais email, mauvais id).

## Telltale Evidence

- Si la reponse reste coherente avec ses propres vraies donnees malgre des parametres faux, les parametres sont cosmetiques/ignores — PAS de faille, juste un parametre non utilise.

## Escalation Order

1. Avant tout test cross-compte (session A + identifiants de B), faire le test de controle: sa propre session + parametres volontairement faux.
2. Si la reponse change en fonction des faux parametres (erreur differente, donnees differentes), les parametres SONT pris en compte — le test cross-compte devient alors probant.
3. Si la reponse reste identique a ses propres vraies donnees malgre des parametres faux, les parametres sont ignores — ne PAS soumettre un IDOR, la reponse cross-compte observee anterieurement avait la meme cause (parametres ignores), pas un defaut d'autorisation.

## Common Mistakes

- Soumettre un IDOR sur la seule base qu'une requete cross-compte renvoie 'not_found' au lieu d'une erreur d'autorisation, sans avoir fait le test de controle avec de faux parametres sur sa propre session — les deux causes (pas de verification d'autorisation vs parametres totalement ignores) produisent exactement la meme reponse observee.

## Payload Shapes

```text
GET /api/status?email=<propre_email_mais_faux>&id=<faux_id>  (depuis sa propre session) -- comparer a la vraie requete
```

## Related Writeups

- N/A — nuance complementaire au pattern deja capture aarme-idor-status-session-only-check (preuve d'IDOR par delta d'erreur anonyme vs authentifie)

## Skill Impact

- Related skill: web-triage (IDOR/BOLA): ajouter le test de controle par faux parametres comme etape obligatoire AVANT de soumettre tout finding IDOR base sur des parametres.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
