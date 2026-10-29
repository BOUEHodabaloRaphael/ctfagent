---
doc_kind: writeup
title: "Zephyr - zsm.local - Shadow Credentials (Whisker/Rubeus) sur un compte machine"
category: web
slug: zephyr-zsm-local-shadow-credentials-mgmt1
created: 2026-10-29
status: solved
tags:
  - shadow-credentials
  - whisker
  - rubeus
  - pkinit
  - adcs
source: "HTB Pro Lab Zephyr"
target: "Compte machine AD avec AddKeyCredentialLink"
---
# Zephyr - zsm.local - Shadow Credentials (Whisker/Rubeus) sur un compte machine

## Challenge Summary

- Source: HTB Pro Lab Zephyr
- Target: Compte machine AD avec AddKeyCredentialLink
- Goal: BloodHound revele une chaine AddKeyCredentialLink sur un compte machine. Whisker ajoute un Shadow Credential (certificat), puis Rubeus PKINIT obtient un TGT + hash NTLM via U2U.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. BloodHound documente le chemin AddKeyCredentialLink.
2. Migration de process pour contourner UAC.
3. Whisker.exe add /target:<compte machine> genere un certificat.
4. Rubeus.exe asktgt /certificate:... /getcredentials -> NTLM du compte machine.

## Key Evidence

- Whisker confirme l'ajout de l'attribut msDS-KeyCredentialLink; Rubeus confirme le TGT request successful et affiche le hash NTLM.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
Whisker.exe, Rubeus.exe asktgt (PKINIT).
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout (lecture visuelle verifiee).

## Reusable Lessons

- Shadow Credentials (msDS-KeyCredentialLink) via l'edge AddKeyCredentialLink est une technique moderne tres reutilisable contre comptes machine/utilisateur.

## Pattern Candidates

- Voir pattern associe de meme slug.
