---
doc_kind: pattern
title: "ESC7 (ManageCA+ManageCertificates) pour forcer l'emission d'un certificat Administrator"
category: misc
slug: intercept-esc7-adcs-managecerts-pkinit
created: 2026-10-29
status: active
tags:
  - esc7
  - adcs
  - managecerts
  - certipy
  - pkinit
  - genericall-group
chain_summary: "ManageCA (via GenericAll sur le groupe CA managers) combine a ManageCertificates permet de forcer l'emission d'une requete de certificat initialement refusee, donnant un certificat pour n'importe quel UPN/SID exploitable par PKINIT."
---
# ESC7 (ManageCA+ManageCertificates) pour forcer l'emission d'un certificat Administrator

## Chain Summary

- One-line chain: ManageCA (via GenericAll sur le groupe CA managers) combine a ManageCertificates permet de forcer l'emission d'une requete de certificat initialement refusee, donnant un certificat pour n'importe quel UPN/SID exploitable par PKINIT.
- Typical target shape: Droit GenericAll sur un groupe donnant acces ManageCA sur le CA du domaine, ou droit ManageCA direct; capacite a devenir officer (ManageCertificates).

## Preconditions

- Droit GenericAll sur un groupe donnant acces ManageCA sur le CA du domaine, ou droit ManageCA direct; capacite a devenir officer (ManageCertificates).

## Cheap Probes

- certipy find pour enumerer les droits sur le CA et les templates; verifier GenericAll sur les groupes lies au CA.

## Telltale Evidence

- Le compte attaquant peut s'ajouter a un groupe donnant ManageCA, confirme par certipy find.

## Escalation Order

1. S'ajouter au groupe donnant ManageCA via l'abus GenericAll.
2. S'ajouter comme officer (ManageCertificates) sur le CA.
3. Activer un template exploitable (ex: SubCA) normalement desactive.
4. Soumettre une requete de certificat avec UPN ET SID du compte cible (Administrator).
5. Meme refusee, forcer l'emission via le droit ManageCertificates (issue-request) avec le Request ID obtenu.
6. Recuperer le certificat et s'authentifier via PKINIT.

## Common Mistakes

- Omettre le parametre -sid dans la requete certipy req (UPN seul), ce qui fait echouer PKINIT avec un message d'erreur trompeur ne pointant pas vers la vraie cause.

## Payload Shapes

```text
certipy req -u <user> -p <pass> -ca <ca> -template SubCA -upn administrator@domain -sid <SID-500>  puis  certipy ca -issue-request <id>
```

## Related Writeups

- intercept-esc7-adcs-managecerts-pkinit

## Skill Impact

- Related skill: pwn-triage/AD CS: ajouter ESC7 (ManageCA+ManageCertificates, emission forcee) comme chemin de privesc complet avec le rappel du parametre -sid obligatoire.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
