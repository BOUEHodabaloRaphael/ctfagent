---
doc_kind: writeup
title: "Tengu - vol de ruches, dechiffrement DPAPI SYSTEM puis Kerberos vers le DC"
category: misc
slug: tengu-dpapi-protected-users-dc
created: 2026-10-29
status: solved
tags:
  - dpapi
  - protected-users
  - kerberos-mandatory
  - secretsdump-local
  - domain-admin
source: "HTB Pro Lab Tengu"
target: "DPAPI profil SYSTEM + compte Protected Users"
---
# Tengu - vol de ruches, dechiffrement DPAPI SYSTEM puis Kerberos vers le DC

## Challenge Summary

- Source: HTB Pro Lab Tengu
- Target: DPAPI profil SYSTEM + compte Protected Users
- Goal: Depuis SYSTEM, dump des ruches puis dechiffrement d'une credential DPAPI du profil SYSTEM revele un compte Domain Admin; ce compte etant dans Protected Users, l'authentification se fait obligatoirement en Kerberos.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. reg save des ruches -> secretsdump.py LOCAL -> hash admin local + DPAPI_SYSTEM keys.
2. Localisation du blob credential et de sa masterkey dans le profil SYSTEM.
3. impacket-dpapi masterkey (deriver manuellement HMAC-SHA1 si bug du protecteur SHA-1).
4. impacket-dpapi credential -> identite + mot de passe d'un compte Domain Admin.
5. impacket-getTGT (NTLM refuse, STATUS_ACCOUNT_RESTRICTION car Protected Users) -> TGT Kerberos.
6. impacket-psexec -k -no-pass -> SYSTEM sur le DC.

## Key Evidence

- Echec NTLM explicite (STATUS_ACCOUNT_RESTRICTION) confirmant Protected Users; identite + mot de passe extraits du blob DPAPI.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
impacket-dpapi masterkey/credential; impacket-getTGT + psexec -k -no-pass.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Dechiffrement DPAPI du profil SYSTEM pour des creds de tache planifiee est un vecteur classique post-SYSTEM; pour protecteur SHA-1 sur une version impacket buguee, deriver manuellement HMAC-SHA1(UserKey, SID) plutot que l'auto-detection.

## Pattern Candidates

- Voir pattern associe de meme slug.
