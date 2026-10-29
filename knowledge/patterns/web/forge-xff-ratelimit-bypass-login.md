---
doc_kind: pattern
title: "Bypass de rate-limit par rotation du header X-Forwarded-For"
category: web
slug: forge-xff-ratelimit-bypass-login
created: 2026-10-29
status: active
tags:
  - rate-limit-bypass
  - x-forwarded-for
  - brute-force
  - auth
chain_summary: "Un rate-limiter qui cle son compteur sur X-Forwarded-For sans valider la chaine de proxy de confiance est contourne en envoyant une valeur differente a chaque requete, rendant le throttling inutile."
---
# Bypass de rate-limit par rotation du header X-Forwarded-For

## Chain Summary

- One-line chain: Un rate-limiter qui cle son compteur sur X-Forwarded-For sans valider la chaine de proxy de confiance est contourne en envoyant une valeur differente a chaque requete, rendant le throttling inutile.
- Typical target shape: Endpoint sensible (login, reset password, OTP) protege uniquement par un rate-limit base sur l'IP extraite d'un header client (X-Forwarded-For, X-Real-IP) sans validation de la source du header.

## Preconditions

- Endpoint sensible (login, reset password, OTP) protege uniquement par un rate-limit base sur l'IP extraite d'un header client (X-Forwarded-For, X-Real-IP) sans validation de la source du header.

## Cheap Probes

- Envoyer plusieurs requetes identiques avec un X-Forwarded-For different (aleatoire) a chaque fois et verifier si le seuil de blocage attendu est atteint.

## Telltale Evidence

- Aucun blocage/429 n'apparait malgre un nombre de requetes largement superieur au seuil observe sans header spoofe.

## Escalation Order

1. Confirmer le rate-limit de base sans header (baseline, seuil de blocage observe).
2. Reexecuter les memes requetes en variant X-Forwarded-For (ou X-Real-IP, Forwarded) a chaque appel.
3. Confirmer l'absence de blocage malgre le depassement du seuil baseline.
4. Evaluer l'impact (brute-force credential, OTP, reset password) selon l'endpoint protege.

## Common Mistakes

- Faire confiance a un header client pour determiner l'IP source du rate-limiting sans allow-list de proxy de confiance avec profondeur fixee, ni compteur complementaire par identifiant de compte/cible.

## Payload Shapes

```text
POST /auth/login  Headers: X-Forwarded-For: <ip aleatoire a chaque requete>
```

## Related Writeups

- forge-xff-ratelimit-bypass-login

## Skill Impact

- Related skill: web-triage (auth/rate-limit): ajouter le test systematique de rotation de header IP sur tout endpoint sensible proteg uniquement par rate-limit IP-based.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
