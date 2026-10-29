---
doc_kind: writeup
title: "Endgame XEN - Doppelganger (password spray comptes de service + RDP DC)"
category: misc
slug: xen-doppelganger-bloodhound-password-spray
created: 2026-10-29
status: solved
tags:
  - bloodhound
  - password-spray
  - service-accounts
  - rdp
  - ad-recon
source: "HTB Endgame XEN"
target: "Comptes de service AD *-svc"
---
# Endgame XEN - Doppelganger (password spray comptes de service + RDP DC)

## Challenge Summary

- Source: HTB Endgame XEN
- Target: Comptes de service AD *-svc
- Goal: Reutilisation d'un mot de passe de compte de service across plusieurs comptes *-svc similaires decouverts via BloodHound, confirmee par password spray, menant a un acces RDP direct sur le DC.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. SharpHound deja collecte depuis le foothold initial; reexamen avec creds existantes montre des comptes *-svc.
2. crackmapexec smb -u svc-accounts.txt -p '<mdp>' --continue-on-success -> plusieurs comptes valides avec le meme mot de passe.
3. BloodHound indique qu'un de ces comptes a un acces RDP direct sur le DC.
4. xfreerdp avec ce compte -> session RDP -> flag sur le bureau.

## Key Evidence

- crackmapexec liste plusieurs comptes *-svc valides simultanement avec le meme mot de passe.

## Dead Ends

- n/a (see Reusable Lessons for pitfalls encountered)

## Payloads And Commands

```text
password spray cible (une liste de comptes de service, un seul mot de passe).
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Les comptes de service partagent souvent le meme mot de passe; un password spray cible sur *-svc apres un premier succes partiel est rentable, puis BloodHound identifie lequel a un edge d'acces (RDP/AdminTo) exploitable.

## Pattern Candidates

- Nouveau pattern: xen-doppelganger-bloodhound-password-spray
