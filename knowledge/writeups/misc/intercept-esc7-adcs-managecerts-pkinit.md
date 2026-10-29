---
doc_kind: writeup
title: "Intercept - Flag Intercept Master (ESC7 ManageCA/ManageCertificates -> PKINIT -> Domain Admin)"
category: misc
slug: intercept-esc7-adcs-managecerts-pkinit
created: 2026-10-29
status: solved
tags:
  - esc7
  - adcs
  - managecerts
  - certipy
  - pkinit
  - genericall-group
source: "HTB Pro Lab Intercept"
target: "AD CS (Certificate Authority) du domaine"
---
# Intercept - Flag Intercept Master (ESC7 ManageCA/ManageCertificates -> PKINIT -> Domain Admin)

## Challenge Summary

- Source: HTB Pro Lab Intercept
- Target: AD CS (Certificate Authority) du domaine
- Goal: Un GenericAll sur un groupe permet de s'y ajouter pour obtenir ManageCA sur le CA; en combinant officer (ManageCertificates) et activation d'un template, une requete refusee est forcee et emise manuellement, donnant un certificat Administrator exploitable par PKINIT.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. net rpc group addmem exploite un GenericAll sur un groupe pour s'y ajouter.
2. certipy ca -add-officer donne le droit ManageCertificates sur le CA.
3. certipy ca -enable-template active un template normalement reserve/desactive (ex: SubCA).
4. certipy req avec un UPN et un SID Administrator -> requete refusee mais Request ID conserve.
5. certipy ca -issue-request force l'emission malgre le refus initial.
6. certipy req -retrieve recupere le certificat+cle.
7. certipy auth -pfx -> PKINIT -> hash NT de l'Administrateur -> acces SMB avec le hash -> flag.

## Key Evidence

- la requete certipy req initiale, bien que refusee, retourne explicitement un Request ID, condition necessaire pour l'emission forcee suivante.

## Dead Ends

- n/a (see Reusable Lessons for pitfalls encountered)

## Payloads And Commands

```text
requete de certificat AD CS (certipy) avec UPN+SID spoofe, emission forcee via droits ManageCertificates.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- ESC7 = ManageCA (ajout d'officer + activation de template) combine a ManageCertificates (forcer l'emission d'une requete refusee) = authentification PKINIT comme n'importe quel compte; fournir systematiquement -sid en plus de -upn dans certipy req, sinon PKINIT echoue avec un message trompeur.

## Pattern Candidates

- Nouveau pattern: intercept-esc7-adcs-managecerts-pkinit
