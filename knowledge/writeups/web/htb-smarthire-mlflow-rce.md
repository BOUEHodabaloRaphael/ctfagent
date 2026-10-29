---
doc_kind: writeup
title: "HTB SmartHire (Medium)"
category: web
slug: htb-smarthire-mlflow-rce
created: 2026-10-29
status: solved
tags:
  - web
  - mlflow
  - pickle-rce
  - deserialization
  - default-creds
  - pth-privesc
source: HackTheBox
target: "MLflow (models.smarthire.htb) + Flask scoring app"
---
# HTB SmartHire (Medium)

## Challenge Summary

- Source: HackTheBox
- Target: MLflow (models.smarthire.htb) + Flask scoring app
- Goal: Credentials MLflow par defaut permettent d'ecraser un artefact pickle et d'obtenir RCE via deserialisation a l'appel de /predict; privesc root via .pth charge par un script sudo NOPASSWD.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. App Flask 'SmartHIRE' (scoring CV), indice MLflow dans le marketing.
2. Fuzzing Host-header -> models.smarthire.htb = 401 Basic Auth MLflow.
3. Auth reussie admin:password (credentials par defaut MLflow).
4. Localisation artefact python_model.pkl (cloudpickle) via API MLflow.
5. Objet pickle malveillant (__reduce__ -> os.system(reverse shell)) ecrasant l'artefact via PUT sur l'API proxy (ecriture non protegee au-dela de Basic Auth).
6. Appel /predict declenche le reload -> shell svcweb.
7. sudo -l: NOPASSWD sur mlflowctl.py qui charge des plugins via site.addsitedir() sur dossier groupe-writable.
8. Depot d'un .pth 'import os; exec(...)' dans plugins/dev/ -> execution root au prochain appel sudo.

## Key Evidence

- 401 Basic realm="mlflow"; taille artefact changee apres PUT; erreur app confirmant l'execution de os.system(); sudoers NOPASSWD sur mlflowctl.py; uid=0(root) final.

## Dead Ends

- n/a.

## Payloads And Commands

```text
Objet pickle __reduce__ -> (os.system,(cmd,)); fichier .pth une ligne 'import os; exec(compile(open(...).read(),...))'.
```

## Flag / Outcome

- user + root flags obtenus.

## Reusable Lessons

- MLflow avec credentials par defaut + API d'ecriture d'artefacts non protegee = RCE via pickle/cloudpickle. site.addsitedir()/.pth sur dossier groupe-writable charge par un script sudo NOPASSWD = privesc root generique.

## Pattern Candidates

- Nouveau pattern: mlflow-default-creds-pickle-rce
