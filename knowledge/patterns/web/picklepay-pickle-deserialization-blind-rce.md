---
doc_kind: pattern
title: "ThunderCipher PicklePay - deserialisation Python pickle via coupon base64 et RCE en aveugle par exception"
category: web
slug: picklepay-pickle-deserialization-blind-rce
created: 2026-10-29
status: active
tags:
  - pickle-deserialization
  - reduce-rce
  - error-based-exfiltration
  - gtfobins-pip3
chain_summary: "Le systeme de coupon decode un blob base64 directement avec pickle.loads, offrant une RCE via __reduce__; sans canal de sortie direct, la technique leve une Exception contenant le resultat de la commande."
---
# ThunderCipher PicklePay - deserialisation Python pickle via coupon base64 et RCE en aveugle par exception

## Chain Summary

- One-line chain: Le systeme de coupon decode un blob base64 directement avec pickle.loads, offrant une RCE via __reduce__; sans canal de sortie direct, la technique leve une Exception contenant le resultat de la commande.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Message d'erreur confirmant pickle; sortie de commande apparaissant dans le champ "detail" de la reponse JSON d'erreur.

## Escalation Order

1. Hint: les coupons sont des blobs base64.
2. POST coupon bidon -> erreur confirmant pickle.loads.
3. Classe Python __reduce__ -> (exec, (code,)) en base64 -> sortie dans le message d'erreur (RCE confirmee).
4. Payload exec avec popen().read() puis raise Exception(result) pour exfiltrer toute commande.
5. sudo -l (meme canal) -> NOPASSWD pip3.
6. Package local setup.py malveillant; sudo pip3 install <dossier> execute en root -> flag.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste (voir lecon ci-dessous).

## Payload Shapes

```text
Pattern generique de RCE aveugle par deserialisation: sans canal de sortie direct, encapsuler la commande dans une Exception(resultat) pour exfiltration via message d'erreur; pip3 sudo NOPASSWD = root via setup.py de package local.
```

## Related Writeups

- picklepay-pickle-deserialization-blind-rce

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
