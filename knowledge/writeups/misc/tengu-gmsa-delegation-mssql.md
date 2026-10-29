---
doc_kind: writeup
title: "Tengu - lecture gMSA puis delegation contrainte S4U vers MSSQL"
category: misc
slug: tengu-gmsa-delegation-mssql
created: 2026-10-29
status: solved
tags:
  - gmsa
  - constrained-delegation
  - s4u2proxy
  - godpotato
  - kerberos-pivot
source: "HTB Pro Lab Tengu"
target: "gMSA avec delegation contrainte vers MSSQL"
---
# Tengu - lecture gMSA puis delegation contrainte S4U vers MSSQL

## Challenge Summary

- Source: HTB Pro Lab Tengu
- Target: gMSA avec delegation contrainte vers MSSQL
- Goal: Le keytab de la machine Linux integree a l'AD permet d'obtenir un TGT et de lire en LDAP l'attribut msDS-ManagedPassword d'un gMSA (hash NT = MD4 des 256 premiers octets du blob); ce gMSA possede une delegation contrainte avec transition de protocole vers MSSQL.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Pivot SOCKS via chisel depuis le webshell.
2. impacket-getTGT avec les creds machine -> TGT machine.
3. Lecture LDAP Kerberos de msDS-ManagedPassword du gMSA -> hash NT = MD4(blob[:256]).
4. impacket-getST avec impersonation (S4U2Self+S4U2Proxy, delegation contrainte + transition de protocole) -> ticket pour le compte cible.
5. impacket-mssqlclient -k -no-pass -> xp_cmdshell.
6. Upload GodPotato (SeImpersonate) -> SYSTEM.

## Key Evidence

- Hash NT du gMSA derive par MD4 du blob 256 octets (pas le decodage string direct); ticket obtenu; whoami SYSTEM apres GodPotato.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
impacket-getTGT / getST (S4U2Self+S4U2Proxy); GodPotato.exe -cmd.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Tout compte lisant msDS-ManagedPassword d'un gMSA avec delegation contrainte+transition de protocole permet d'usurper un compte cible via S4U2Self puis S4U2Proxy vers le SPN autorise; ne jamais cibler un compte T0/Protected Users pour l'impersonation.

## Pattern Candidates

- Voir pattern associe de meme slug.
