---
doc_kind: pattern
title: "OAuth state binding opt-in = login CSRF par omission du binding"
category: web
slug: forge-oauth-login-csrf-state-binding-optional
created: 2026-10-29
status: active
tags:
  - oauth
  - csrf
  - login-csrf
  - pkce-state
  - opt-in-security-control
chain_summary: "Quand le lien cryptographique entre le state OAuth et la session navigateur depend d'un parametre optionnel a l'initiation, l'attaquant initie simplement le flux sans ce parametre pour desactiver la protection."
---
# OAuth state binding opt-in = login CSRF par omission du binding

## Chain Summary

- One-line chain: Quand le lien cryptographique entre le state OAuth et la session navigateur depend d'un parametre optionnel a l'initiation, l'attaquant initie simplement le flux sans ce parametre pour desactiver la protection.
- Typical target shape: Flux OAuth/OIDC ou le binding state<->session est controlable par un parametre d'initiation (pas impose systematiquement par le serveur).

## Preconditions

- Flux OAuth/OIDC ou le binding state<->session est controlable par un parametre d'initiation (pas impose systematiquement par le serveur).

## Cheap Probes

- Initier le flux OAuth sans tous les parametres optionnels documentes et verifier si le state genere contient toujours un claim de liaison a la session.

## Telltale Evidence

- Le state genere sans le parametre optionnel ne contient pas de claim de session; le callback l'accepte tout de meme sans le verifier.

## Escalation Order

1. Initier le flux OAuth en omettant le parametre de binding optionnel.
2. Completer le flux avec le compte attaquant, capturer code+state.
3. Envoyer ce code+state a la victime via un lien de callback.
4. Confirmer que la victime est authentifiee sous le compte attaquant.

## Common Mistakes

- Rendre une protection de securite critique (binding state<->session) opt-in plutot que systematique et imposee serveur-side.

## Payload Shapes

```text
GET /callback?code=<attacker-code>&state=<unbound-state>  (envoye a la victime)
```

## Related Writeups

- forge-oauth-login-csrf-state-binding-optional

## Skill Impact

- Related skill: web-triage (OAuth): ajouter test systematique 'initier le flux sans les parametres de securite optionnels' pour tout flux OAuth/OIDC.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
