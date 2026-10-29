---
doc_kind: writeup
title: "Endgame HADES - Dominion (reutilisation de mot de passe + Kerberos vers Domain Admin malgre Protected Users)"
category: misc
slug: hades-dominion-password-reuse-protected-users
created: 2026-10-29
status: solved
tags:
  - protected-users
  - kerberos-only
  - password-reuse
  - clock-skew
  - domain-admin
source: "HTB Endgame HADES"
target: "Compte Administrator domaine, membre Protected Users"
---
# Endgame HADES - Dominion (reutilisation de mot de passe + Kerberos vers Domain Admin malgre Protected Users)

## Challenge Summary

- Source: HTB Endgame HADES
- Target: Compte Administrator domaine, membre Protected Users
- Goal: Le compte administrator du domaine, membre du groupe Protected Users (NTLM refuse), reutilise le meme mot de passe que l'administrateur local d'une autre machine; apres synchronisation d'horloge, un TGT est obtenu.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Constat: administrator appartient a Protected Users -> seul Kerberos fonctionne, pas de pass-the-hash/NTLM.
2. Le mot de passe admin local deja decouvert est reutilise pour le compte de domaine.
3. Synchronisation de l'horloge locale (tolerance Kerberos < 5 min).
4. impacket-getTGT obtient un TGT valide avec ces creds.
5. impacket-smbclient avec le TGT -> acces C$ sur le DC -> flag final.

## Key Evidence

- impacket-getTGT reussit et sauvegarde un ccache, confirmant que le mot de passe reutilise est valide malgre Protected Users.

## Dead Ends

- n/a (see Reusable Lessons for pitfalls encountered)

## Payloads And Commands

```text
obtention de TGT Kerberos (getTGT) apres resynchronisation d'horloge systeme.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Le groupe Protected Users bloque NTLM/delegation mais pas une authentification Kerberos standard avec mot de passe correct; une erreur d'horloge (skew > 5 min) peut faire echouer silencieusement du Kerberos valide - toujours synchroniser l'heure avant de conclure a un echec d'authentification Kerberos.

## Pattern Candidates

- Nouveau pattern: hades-dominion-password-reuse-protected-users
