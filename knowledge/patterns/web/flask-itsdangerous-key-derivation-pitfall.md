---
doc_kind: pattern
title: "Piege crack de cookie Flask itsdangerous: key_derivation hmac vs django-concat"
category: web
slug: flask-itsdangerous-key-derivation-pitfall
created: 2026-10-30
status: active
tags:
  - legacy-memory-migration
  - nctf26-prep
  - flask
chain_summary: "itsdangerous (lib de signature de cookies) utilise par defaut key_derivation=django-concat, PAS hmac comme Flask — un script de crack qui ne precise pas explicitement signer_kwargs={key_derivation:hmac, digest_method:sha1} teste le MAUVAIS algorithme et ne peut jamais matcher, meme avec le bon mot dans la wordlist."
---
# Piege crack de cookie Flask itsdangerous: key_derivation hmac vs django-concat

## Chain Summary

- One-line chain: itsdangerous (lib de signature de cookies) utilise par defaut key_derivation=django-concat, PAS hmac comme Flask — un script de crack qui ne precise pas explicitement signer_kwargs={key_derivation:hmac, digest_method:sha1} teste le MAUVAIS algorithme et ne peut jamais matcher, meme avec le bon mot dans la wordlist.

## Preconditions

- Cookie de session Flask signe (itsdangerous) a cracker (ex. via flask-unsign).

## Cheap Probes

- Verifier explicitement les signer_kwargs utilises par le script de crack avant de lancer une wordlist longue.

## Telltale Evidence

- Un crack epuisant rockyou.txt (14M+ mots) + plusieurs wordlists ciblees sans jamais matcher, alors que le bon mot existe dans une des wordlists testees — signal fort d'un mauvais algorithme de derivation plutot que d'un mauvais mot de passe.

## Escalation Order

1. Avant tout crack long, verifier explicitement que le script/outil utilise signer_kwargs={'key_derivation': 'hmac', 'digest_method': hashlib.sha1} (le comportement Flask reel).
2. Si l'outil utilise les parametres par defaut d'itsdangerous (key_derivation='django-concat'), le crack testera systematiquement le MAUVAIS algorithme et ne pourra jamais trouver le bon secret, quelle que soit la wordlist.
3. Re-tester avec les bons signer_kwargs explicites avant d'epuiser des wordlists supplementaires ou de conclure a un echec.

## Common Mistakes

- Epuiser des wordlists de plus en plus larges contre un cookie Flask sans d'abord verifier que l'outil de crack utilise bien key_derivation=hmac explicitement (le defaut itsdangerous est django-concat, different de Flask).

## Payload Shapes

```text
flask-unsign --unsign --cookie '<cookie>' --wordlist rockyou.txt  (verifier le support hmac explicite dans l'outil utilise)
```

## Related Writeups

- N/A

## Skill Impact

- Related skill: web-triage: ajouter la verification key_derivation=hmac comme etape obligatoire avant tout crack de cookie Flask itsdangerous.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
