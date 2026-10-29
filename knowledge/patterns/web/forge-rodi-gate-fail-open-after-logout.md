---
doc_kind: pattern
title: "Garde fail-open quand le cache d'autorisation est absent plutot que revalide"
category: web
slug: forge-rodi-gate-fail-open-after-logout
created: 2026-10-29
status: active
tags:
  - broken-access-control
  - fail-open
  - session-not-revoked
  - business-logic
chain_summary: "Un controle d'autorisation qui traite un cache absent (None/non defini) comme 'rien a bloquer' plutot que de forcer une revalidation live devient un fail-open exploitable en invalidant volontairement ce cache via une action non liee (ex: logout)."
---
# Garde fail-open quand le cache d'autorisation est absent plutot que revalide

## Chain Summary

- One-line chain: Un controle d'autorisation qui traite un cache absent (None/non defini) comme 'rien a bloquer' plutot que de forcer une revalidation live devient un fail-open exploitable en invalidant volontairement ce cache via une action non liee (ex: logout).
- Typical target shape: Controle d'autorisation (quota, capacite payante, role) s'appuyant sur une valeur mise en cache qui peut etre invalidee/videe par une action utilisateur legitime (logout, refresh, etc.).

## Preconditions

- Controle d'autorisation (quota, capacite payante, role) s'appuyant sur une valeur mise en cache qui peut etre invalidee/videe par une action utilisateur legitime (logout, refresh, etc.).

## Cheap Probes

- Apres une action qui devrait vider un cache d'etat (logout, changement de session), retenter immediatement l'action protegee avec le meme contexte d'authentification s'il reste valide.

## Telltale Evidence

- Le controle ne leve aucune erreur/refus apres l'invalidation du cache, alors qu'il refusait correctement avant.

## Escalation Order

1. Identifier un garde d'autorisation qui depend d'un etat mis en cache (solde, quota, role).
2. Identifier une action qui vide ce cache sans revoquer la session/le token (souvent logout ou un endpoint de rafraichissement).
3. Declencher cette action puis retenter l'action protegee avec les memes credentials/token.
4. Confirmer que le controle passe silencieusement en l'absence de cache plutot que de forcer une revalidation.

## Common Mistakes

- Coder un garde qui 'return si cache absent' au lieu de 'revalider depuis la source de verite si cache absent'.

## Payload Shapes

```text
POST /auth/logout (meme token) puis POST /gated-endpoint (meme token)
```

## Related Writeups

- forge-rodi-gate-fail-open-after-logout, forge-security-review-rodi-gate-bypass

## Skill Impact

- Related skill: web-triage (business logic): ajouter le test 'invalider un cache d'autorisation via une action adjacente puis retenter l'action protegee' comme sous-cas de fail-open.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
