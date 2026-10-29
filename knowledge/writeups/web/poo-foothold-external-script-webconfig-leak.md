---
doc_kind: writeup
title: "P.O.O. - Foothold (sp_execute_external_script + credential en commentaire web.config)"
category: web
slug: poo-foothold-external-script-webconfig-leak
created: 2026-10-29
status: solved
tags:
  - mssql
  - sp_execute_external_script
  - web-config-leak
  - http-basic-auth
  - context-switch
source: "HTB Mini Pro Lab P.O.O."
target: "MSSQL + IIS web.config"
---
# P.O.O. - Foothold (sp_execute_external_script + credential en commentaire web.config)

## Challenge Summary

- Source: HTB Mini Pro Lab P.O.O.
- Target: MSSQL + IIS web.config
- Goal: Le compte de service SQL ne peut pas lire web.config directement, mais sp_execute_external_script execute sous un autre utilisateur qui a les droits; web.config revele un mot de passe admin en clair dans un bloc commente.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Tentative directe de lecture via xp_cmdshell -> acces refuse.
2. sp_execute_external_script @language=N'Python' lit le fichier sous un autre contexte utilisateur -> succes.
3. web.config commente revele des credentials admin en clair.
4. Le mapping MIME dans le meme fichier confirme pourquoi .DS_Store etait servi.
5. Acces a une zone admin (HTTP Basic) avec ces creds.

## Key Evidence

- contenu XML commente contenant un bloc d'authentification Forms avec credentials en clair.

## Dead Ends

- n/a (see Reusable Lessons for pitfalls encountered)

## Payloads And Commands

```text
appel sp_execute_external_script en Python pour contourner une restriction de lecture de fichier.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- sp_execute_external_script change le contexte d'execution (autre compte OS) et peut contourner des restrictions NTFS qu'un compte SQL direct n'a pas; toujours tester plusieurs contextes d'execution avant de conclure a un acces refuse definitif.

## Pattern Candidates

- Nouveau pattern: poo-foothold-external-script-webconfig-leak
