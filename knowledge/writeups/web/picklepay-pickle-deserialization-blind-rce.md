---
doc_kind: writeup
title: "ThunderCipher PicklePay - deserialisation Python pickle via coupon base64 et RCE en aveugle par exception"
category: web
slug: picklepay-pickle-deserialization-blind-rce
created: 2026-10-29
status: solved
tags:
  - pickle-deserialization
  - reduce-rce
  - error-based-exfiltration
  - gtfobins-pip3
source: thundercipher.in/labs
target: "Systeme de coupon pickle.loads"
---
# ThunderCipher PicklePay - deserialisation Python pickle via coupon base64 et RCE en aveugle par exception

## Challenge Summary

- Source: thundercipher.in/labs
- Target: Systeme de coupon pickle.loads
- Goal: Le systeme de coupon decode un blob base64 directement avec pickle.loads, offrant une RCE via __reduce__; sans canal de sortie direct, la technique leve une Exception contenant le resultat de la commande.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Hint: les coupons sont des blobs base64.
2. POST coupon bidon -> erreur confirmant pickle.loads.
3. Classe Python __reduce__ -> (exec, (code,)) en base64 -> sortie dans le message d'erreur (RCE confirmee).
4. Payload exec avec popen().read() puis raise Exception(result) pour exfiltrer toute commande.
5. sudo -l (meme canal) -> NOPASSWD pip3.
6. Package local setup.py malveillant; sudo pip3 install <dossier> execute en root -> flag.

## Key Evidence

- Message d'erreur confirmant pickle; sortie de commande apparaissant dans le champ "detail" de la reponse JSON d'erreur.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
Objet Python __reduce__ -> (exec, (code,)) serialise pickle+base64; setup.py GTFOBins pour pip3.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Pattern generique de RCE aveugle par deserialisation: sans canal de sortie direct, encapsuler la commande dans une Exception(resultat) pour exfiltration via message d'erreur; pip3 sudo NOPASSWD = root via setup.py de package local.

## Pattern Candidates

- Voir pattern associe de meme slug.
