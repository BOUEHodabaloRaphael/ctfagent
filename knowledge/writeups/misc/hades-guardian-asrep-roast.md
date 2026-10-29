---
doc_kind: writeup
title: "Endgame HADES - Guardian (AS-REP Roasting d'un compte sans pre-auth)"
category: misc
slug: hades-guardian-asrep-roast
created: 2026-10-29
status: solved
tags:
  - as-rep-roast
  - kerberos-preauth-disabled
  - hashcat-18200
  - getnpusers
source: "HTB Endgame HADES"
target: "Compte AD avec pre-authentification Kerberos desactivee"
---
# Endgame HADES - Guardian (AS-REP Roasting d'un compte sans pre-auth)

## Challenge Summary

- Source: HTB Endgame HADES
- Target: Compte AD avec pre-authentification Kerberos desactivee
- Goal: Un compte de domaine avec la pre-authentification Kerberos desactivee est identifie par enumeration de noms sans authentification LDAP, puis son AS-REP est demande et casse hors-ligne.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Enumeration de noms de comptes probable (sans creds LDAP valides).
2. impacket-GetNPUsers -no-pass sur cette liste -> hash AS-REP pour un compte.
3. hashcat -m 18200 sur une wordlist -> mot de passe casse.
4. nxc smb confirme les creds, acces SMB en lecture sur un partage -> flag.

## Key Evidence

- hash AS-REP casse par hashcat avec statut "Cracked".

## Dead Ends

- n/a (see Reusable Lessons for pitfalls encountered)

## Payloads And Commands

```text
requete AS-REQ sans pre-auth (GetNPUsers) + crack offline hashcat mode 18200.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Meme sans acces LDAP authentifie, une liste de noms d'utilisateurs plausibles suffit pour tenter un AS-REP roast; c'est une des rares attaques Kerberos ne necessitant aucune authentification prealable.

## Pattern Candidates

- Nouveau pattern: hades-guardian-asrep-roast
