---
doc_kind: writeup
title: "FullHouse - Le Lambda porte le pouvoir (RCE desecurisation modele Keras/TensorFlow)"
category: web
slug: fullhouse-tensorflow-lambda-rce
created: 2026-10-29
status: solved
tags:
  - ml-deserialization
  - keras-lambda-rce
  - model-upload
  - fifo-shell
  - tensorflow
source: "HTB Pro Lab FullHouse"
target: "Endpoint d'upload de modele ML (.h5)"
---
# FullHouse - Le Lambda porte le pouvoir (RCE desecurisation modele Keras/TensorFlow)

## Challenge Summary

- Source: HTB Pro Lab FullHouse
- Target: Endpoint d'upload de modele ML (.h5)
- Goal: L'endpoint d'upload charge un modele Keras (.h5) sans restriction; une couche Lambda contenant du bytecode Python arbitraire s'execute automatiquement au chargement du modele cote serveur, donnant RCE.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Analyse JS du dashboard authentifie revele l'endpoint d'upload de modele.
2. Construction d'un modele tf.keras.Sequential avec une couche Lambda executant os.system.
3. model.save() puis upload via curl multipart avec le cookie de session.
4. Un deuxieme modele declenche l'execution du reverse shell deja telecharge.
5. Listener nc reconstruit via FIFO (contournement du blocage d'un pipe simple sans ecrivain) -> shell obtenu.

## Key Evidence

- upload des modeles renvoie succes, puis le shell confirme l'identite obtenue.

## Dead Ends

- n/a (see Reusable Lessons for pitfalls encountered)

## Payloads And Commands

```text
fichier modele Keras .h5 avec couche Lambda malveillante (deserialisation RCE).
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- tf.keras.layers.Lambda deserialise et execute du bytecode Python arbitraire a l'import du modele: tout endpoint d'upload de modele ML sans sandboxing est une RCE potentielle; pour un reverse shell qui bloque en ecriture sans lecteur, utiliser une FIFO lecture-ecriture au lieu d'un pipe simple.

## Pattern Candidates

- Nouveau pattern: fullhouse-tensorflow-lambda-rce
