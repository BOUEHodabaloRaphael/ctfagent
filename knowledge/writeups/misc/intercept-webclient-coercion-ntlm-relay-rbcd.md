---
doc_kind: writeup
title: "Intercept - Flag Relayed (coercition WebClient/WebDAV -> relais LDAP -> RBCD -> S4U2Proxy)"
category: misc
slug: intercept-webclient-coercion-ntlm-relay-rbcd
created: 2026-10-29
status: solved
tags:
  - petitpotam
  - webclient-webdav
  - ntlm-relay-ldap
  - rbcd
  - s4u2proxy
  - adidns
source: "HTB Pro Lab Intercept"
target: "Compte machine WS01$ + DC01 LDAP"
---
# Intercept - Flag Relayed (coercition WebClient/WebDAV -> relais LDAP -> RBCD -> S4U2Proxy)

## Challenge Summary

- Source: HTB Pro Lab Intercept
- Target: Compte machine WS01$ + DC01 LDAP
- Goal: PetitPotam force un compte machine a s'authentifier en HTTP (WebClient/WebDAV) vers un enregistrement DNS controle; ntlmrelayx relaie vers LDAP avec --delegate-access pour ecrire une delegation RBCD, permettant un S4U2Proxy qui usurpe Administrator.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. dnstool.py ajoute un enregistrement DNS relatif dans l'ADIDNS pointant vers l'IP attaquant.
2. ntlmrelayx lance avec stdin maintenu ouvert, ciblant ldap://DC avec --delegate-access.
3. PetitPotam force le compte machine a s'authentifier via le nom NETBIOS COURT (pas le FQDN) vers l'enregistrement controle.
4. Le relais HTTP->LDAP reussit, cree un compte machine et ecrit une delegation RBCD sur le compte machine cible.
5. impacket-getST impersonnant Administrator avec le nouveau compte machine -> ticket S4U2Proxy.
6. impacket-smbclient avec le ticket -> lecture du flag sur le bureau Administrator de la machine cible.

## Key Evidence

- log ntlmrelayx confirmant l'authentification relayee avec succes puis "Delegation rights modified succesfully!".

## Dead Ends

- n/a (see Reusable Lessons for pitfalls encountered)

## Payloads And Commands

```text
coercition PetitPotam (MS-EFSRPC) ciblant un nom NetBIOS WebDAV + chaine ntlmrelayx --delegate-access (RBCD) + getST S4U2Proxy.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Pour forcer une authentification NTLM exploitable via WebClient/WebDAV, utiliser le nom NetBIOS court jamais le FQDN (le FQDN declenche Kerberos/logon null sans header Authorization NTLM); ntlmrelayx lit sur stdin et quitte immediatement sur EOF, toujours le lancer avec stdin maintenu ouvert.

## Pattern Candidates

- Nouveau pattern: intercept-webclient-coercion-ntlm-relay-rbcd
