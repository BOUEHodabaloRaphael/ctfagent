---
doc_kind: pattern
title: "Prouver un IDOR/BOLA par le delta de code d'erreur (sans donnees tierces reelles)"
category: web
slug: aarme-idor-status-session-only-check
created: 2026-10-29
status: active
tags:
  - idor
  - bola
  - broken-object-level-auth
  - session-only-check
  - cwe-639
chain_summary: "Comparer le code/message d'erreur entre une requete anonyme (unauthenticated) et une requete authentifiee croisee visant les donnees d'un autre compte (not_found/success) prouve l'absence de controle de propriete, meme sans avoir de vraies donnees tierces a lire."
---
# Prouver un IDOR/BOLA par le delta de code d'erreur (sans donnees tierces reelles)

## Chain Summary

- One-line chain: Comparer le code/message d'erreur entre une requete anonyme (unauthenticated) et une requete authentifiee croisee visant les donnees d'un autre compte (not_found/success) prouve l'absence de controle de propriete, meme sans avoir de vraies donnees tierces a lire.
- Typical target shape: Endpoint acceptant un identifiant de ressource (email, id, ref) en parametre cote client, sous une session authentifiee quelconque.

## Preconditions

- Endpoint acceptant un identifiant de ressource (email, id, ref) en parametre cote client, sous une session authentifiee quelconque.

## Cheap Probes

- Requete sans session avec un identifiant quelconque -> noter le message/code d'erreur. Meme requete avec une session authentifiee valide mais visant un identifiant different de celui du compte de la session -> comparer le message/code.

## Telltale Evidence

- Le message d'erreur change entre 'non authentifie' (anonyme) et 'non trouve'/'succes' (authentifie croise), ce qui prouve que la verification d'autorisation metier n'a pas lieu, meme en l'absence de ressource tierce reelle existante.

## Escalation Order

1. Tester l'endpoint sans session pour etablir le message d'erreur de base (absence d'authentification).
2. Tester le meme endpoint avec une session valide mais un identifiant de ressource appartenant a un autre compte.
3. Comparer precisement les deux messages/codes; un changement prouve l'absence de check de propriete, independamment du fait que la ressource existe ou non.

## Common Mistakes

- Conclure a l'absence d'IDOR juste parce qu'aucune donnee tierce reelle n'est accessible pour le test (le delta de code d'erreur suffit a prouver le manque de controle).

## Payload Shapes

```text
GET /api/.../status?email=<victim>&ref=<victim_ref>  (sous session attaquant)
```

## Related Writeups

- aarme-idor-status-session-only-check

## Skill Impact

- Related skill: web-triage (IDOR/BOLA): ajouter la methode 'delta de code d'erreur anonyme vs authentifie-croise' comme preuve minimale d'IDOR sans besoin de donnees tierces reelles.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
