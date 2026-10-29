---
doc_kind: writeup
title: "DANTE DC02 - AS-REP Roasting puis DCSync administrateur"
category: misc
slug: dc02-asrep-roasting-dcsync
created: 2026-10-29
status: solved
tags:
  - asrep-roasting
  - dcsync
  - pass-the-hash
  - kerberos
  - secretsdump
source: "HTB Pro Lab DANTE"
target: "AD avec compte sans pre-auth + droits de replication"
---
# DANTE DC02 - AS-REP Roasting puis DCSync administrateur

## Challenge Summary

- Source: HTB Pro Lab DANTE
- Target: AD avec compte sans pre-auth + droits de replication
- Goal: Un compte a la pre-authentification Kerberos desactivee (AS-REP roasting), menant a un acces utilisateur qui dispose des droits de replication pour un DCSync recuperant le hash NT administrateur.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Password spray/credential test -> premier acces utilisateur confirme.
2. impacket-GetNPUsers -> compte avec preauth desactivee -> hash AS-REP cracke.
3. secretsdump.py -just-dc-user administrator -> hash NT administrateur (DCSync).
4. psexec.py -hashes <NT> (pass-the-hash) -> flag admin, pivot.

## Key Evidence

- Hash NT administrateur recupere via secretsdump (-just-dc-user); session SYSTEM obtenue par psexec -hashes.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
impacket-GetNPUsers (AS-REP roast); secretsdump --just-dc-user; psexec.py -hashes (pass-the-hash).
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- AS-REP roasting sur compte sans preauth + droits de replication (DCSync) = chemin direct vers hash administrateur sans toucher LSASS du DC; reutiliser le hash en pass-the-hash sur toute machine du domaine.

## Pattern Candidates

- Voir pattern associe de meme slug.
