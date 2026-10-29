---
doc_kind: pattern
title: "Tengu - lecture gMSA puis delegation contrainte S4U vers MSSQL"
category: misc
slug: tengu-gmsa-delegation-mssql
created: 2026-10-29
status: active
tags:
  - gmsa
  - constrained-delegation
  - s4u2proxy
  - godpotato
  - kerberos-pivot
chain_summary: "Le keytab de la machine Linux integree a l'AD permet d'obtenir un TGT et de lire en LDAP l'attribut msDS-ManagedPassword d'un gMSA (hash NT = MD4 des 256 premiers octets du blob); ce gMSA possede une delegation contrainte avec transition de protocole vers MSSQL."
---
# Tengu - lecture gMSA puis delegation contrainte S4U vers MSSQL

## Chain Summary

- One-line chain: Le keytab de la machine Linux integree a l'AD permet d'obtenir un TGT et de lire en LDAP l'attribut msDS-ManagedPassword d'un gMSA (hash NT = MD4 des 256 premiers octets du blob); ce gMSA possede une delegation contrainte avec transition de protocole vers MSSQL.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Hash NT du gMSA derive par MD4 du blob 256 octets (pas le decodage string direct); ticket obtenu; whoami SYSTEM apres GodPotato.

## Escalation Order

1. Pivot SOCKS via chisel depuis le webshell.
2. impacket-getTGT avec les creds machine -> TGT machine.
3. Lecture LDAP Kerberos de msDS-ManagedPassword du gMSA -> hash NT = MD4(blob[:256]).
4. impacket-getST avec impersonation (S4U2Self+S4U2Proxy, delegation contrainte + transition de protocole) -> ticket pour le compte cible.
5. impacket-mssqlclient -k -no-pass -> xp_cmdshell.
6. Upload GodPotato (SeImpersonate) -> SYSTEM.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste (voir lecon ci-dessous).

## Payload Shapes

```text
Tout compte lisant msDS-ManagedPassword d'un gMSA avec delegation contrainte+transition de protocole permet d'usurper un compte cible via S4U2Self puis S4U2Proxy vers le SPN autorise; ne jamais cibler un compte T0/Protected Users pour l'impersonation.
```

## Related Writeups

- tengu-gmsa-delegation-mssql

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
