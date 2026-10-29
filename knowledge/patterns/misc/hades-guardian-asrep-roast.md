---
doc_kind: pattern
title: "AS-REP Roasting sans aucune authentification prealable"
category: misc
slug: hades-guardian-asrep-roast
created: 2026-10-29
status: active
tags:
  - as-rep-roast
  - kerberos-preauth-disabled
  - hashcat-18200
  - getnpusers
chain_summary: "Une liste de noms d'utilisateurs plausibles (devinee ou enumeree sans creds) suffit pour tenter un AS-REP roast; les comptes avec pre-auth Kerberos desactivee renvoient directement un hash crackable."
---
# AS-REP Roasting sans aucune authentification prealable

## Chain Summary

- One-line chain: Une liste de noms d'utilisateurs plausibles (devinee ou enumeree sans creds) suffit pour tenter un AS-REP roast; les comptes avec pre-auth Kerberos desactivee renvoient directement un hash crackable.
- Typical target shape: Acces reseau a un DC (port 88 Kerberos); une liste de noms d'utilisateurs candidats, sans besoin de credentials valides.

## Preconditions

- Acces reseau a un DC (port 88 Kerberos); une liste de noms d'utilisateurs candidats, sans besoin de credentials valides.

## Cheap Probes

- impacket-GetNPUsers <domain>/ -usersfile <liste> -no-pass -format hashcat.

## Telltale Evidence

- Au moins un compte de la liste renvoie un hash AS-REP (compte avec pre-auth desactivee).

## Escalation Order

1. Construire une liste de noms d'utilisateurs plausibles (OSINT, convention de nommage, enumeration RID si possible).
2. Lancer GetNPUsers -no-pass sur cette liste.
3. Cracker offline tout hash AS-REP obtenu (hashcat -m 18200).
4. Valider les creds obtenues sur SMB/LDAP.

## Common Mistakes

- Supposer qu'un acces LDAP authentifie est necessaire pour tenter un AS-REP roast, alors qu'une simple liste de noms suffit.

## Payload Shapes

```text
GetNPUsers.py domain/ -usersfile users.txt -no-pass -format hashcat -outputfile asrep.hash
```

## Related Writeups

- hades-guardian-asrep-roast

## Skill Impact

- Related skill: pwn-triage/AD: ajouter AS-REP roast sans authentification comme premiere attaque Kerberos a tenter des qu'une liste de noms est disponible.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
