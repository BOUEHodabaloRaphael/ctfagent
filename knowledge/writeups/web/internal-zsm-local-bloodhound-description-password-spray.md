---
doc_kind: writeup
title: "Zephyr - internal domain - Mot de passe en clair dans description AD + password spray"
category: web
slug: internal-zsm-local-bloodhound-description-password-spray
created: 2026-10-29
status: solved
tags:
  - ad
  - description-field
  - password-spray
  - bloodhound
source: "HTB Pro Lab Zephyr"
target: "AD second domaine interne"
---
# Zephyr - internal domain - Mot de passe en clair dans description AD + password spray

## Challenge Summary

- Source: HTB Pro Lab Zephyr
- Target: AD second domaine interne
- Goal: SharpHound revele qu'un compte de service a un mot de passe en clair stocke dans le champ Description. Un spray de ce mot de passe contre tous les utilisateurs du domaine reussit sur un autre compte.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. SharpHound+BloodHound import.
2. Node Info d'un compte de service -> champ Description contient un mot de passe en clair.
3. Wordlist de tous les utilisateurs du domaine.
4. proxychains cme winrm password spray -> succes sur un compte.
5. evil-winrm avec ce compte.

## Key Evidence

- Champ Description BloodHound visible; cme confirme Pwn3d! sur le compte spraye.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
SharpHound, crackmapexec winrm password spray.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout (lecture visuelle verifiee).

## Reusable Lessons

- Toujours verifier les champs Description/Notes AD pour des mots de passe en clair oublies, puis sprayer ce mot de passe sur tous les comptes du domaine.

## Pattern Candidates

- Voir pattern associe de meme slug.
