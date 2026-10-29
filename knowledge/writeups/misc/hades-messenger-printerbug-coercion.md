---
doc_kind: writeup
title: "Endgame HADES - Messenger (coercition MS-RPRN PrinterBug + reutilisation mdp admin local)"
category: misc
slug: hades-messenger-printerbug-coercion
created: 2026-10-29
status: solved
tags:
  - printerbug
  - ms-rprn
  - coercion
  - password-reuse
  - kerberos-local-admin
source: "HTB Endgame HADES"
target: "Service Spooler expose + mot de passe admin local reutilise"
---
# Endgame HADES - Messenger (coercition MS-RPRN PrinterBug + reutilisation mdp admin local)

## Challenge Summary

- Source: HTB Endgame HADES
- Target: Service Spooler expose + mot de passe admin local reutilise
- Goal: Le service Spooler expose permet de forcer une authentification machine (PrinterBug) confirmant la coercition; le mot de passe administrateur local d'une machine est reutilise directement dans le domaine.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. impacket-rpcdump identifie l'interface [MS-RPRN]/spoolsv.exe exposee sur une machine.
2. nxc smb -M coerce_plus METHOD=PrinterBug confirme la coercition reussie.
3. Reutilisation du mot de passe administrateur local valide via Kerberos dans le domaine.
4. Creation d'un partage ouvert pour exfiltrer le flag.
5. Recuperation du flag via ce partage.

## Key Evidence

- nxc affiche "Successfully coerced!" confirmant que la machine s'authentifie bien vers l'hote distant sous identite machine.

## Dead Ends

- n/a (see Reusable Lessons for pitfalls encountered)

## Payloads And Commands

```text
module de coercition PrinterBug (nxc -M coerce_plus) + partage SMB temporaire pour exfiltration.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- rpcdump pour confirmer la presence de [MS-RPRN] avant de lancer une coercition PrinterBug evite les tentatives aveugles; un mot de passe admin local reutilise dans le domaine via Kerberos ouvre un acces d'execution de commande.

## Pattern Candidates

- Nouveau pattern: hades-messenger-printerbug-coercion
