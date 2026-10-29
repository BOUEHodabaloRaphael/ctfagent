---
doc_kind: pattern
title: "MLflow creds par defaut -> RCE pickle -> .pth privesc"
category: web
slug: htb-smarthire-mlflow-rce
created: 2026-10-29
status: active
tags:
  - web
  - mlflow
  - pickle-rce
  - deserialization
  - default-creds
  - pth-privesc
chain_summary: "MLflow avec admin:password + API artefacts non protegee = RCE pickle; .pth sur dossier groupe-writable charge par sudo NOPASSWD = privesc root."
---
# MLflow creds par defaut -> RCE pickle -> .pth privesc

## Chain Summary

- One-line chain: MLflow avec admin:password + API artefacts non protegee = RCE pickle; .pth sur dossier groupe-writable charge par sudo NOPASSWD = privesc root.
- Typical target shape: Service MLflow accessible (souvent sur un sous-domaine vhost separe de l'app principale ML-powered).

## Preconditions

- Service MLflow accessible (souvent sur un sous-domaine vhost separe de l'app principale ML-powered).

## Cheap Probes

- Fuzzer les vhosts/Host-header autour d'une app ML (models.*, mlflow.*, tracking.*); tester admin:password / credentials par defaut documentes MLflow.

## Telltale Evidence

- 401 Basic realm="mlflow"; artefact modele accessible/modifiable via l'API proxy sans controle supplementaire.

## Escalation Order

1. Enumerer les artefacts de modele (pickle/cloudpickle) via l'API MLflow.
2. Ecraser un artefact avec un objet pickle malveillant (__reduce__).
3. Declencher le reload/predict pour executer le payload.
4. Apres shell, chercher des scripts sudo NOPASSWD qui chargent des plugins Python depuis un dossier group-writable (site.addsitedir/.pth).

## Common Mistakes

- S'arreter a l'auth MLflow sans verifier si l'API d'ecriture d'artefacts est elle-meme protegee independamment.

## Payload Shapes

```text
class Evil:\n  def __reduce__(self):\n    return (os.system, ('bash -c ...',))
```

## Related Writeups

- htb-smarthire-mlflow-rce

## Skill Impact

- Related skill: web-triage: ajouter MLflow/credentials par defaut + artefacts pickle comme sous-cas de RCE via deserialisation ML.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
