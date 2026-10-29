---
doc_kind: writeup
title: "Zephyr - Painters.htb - DCSync /history -> mot de passe reutilise -> root sur serveur mail"
category: web
slug: painters-htb-dcsync-history-mail-root
created: 2026-10-29
status: solved
tags:
  - dcsync
  - password-history
  - credential-reuse
source: "HTB Pro Lab Zephyr"
target: "AD painters.htb, serveur mail"
---
# Zephyr - Painters.htb - DCSync /history -> mot de passe reutilise -> root sur serveur mail

## Challenge Summary

- Source: HTB Pro Lab Zephyr
- Target: AD painters.htb, serveur mail
- Goal: Un champ description BloodHound suggere un role admin; DCSync avec /history recupere les anciens mots de passe, reutilises pour se connecter au serveur mail et obtenir root via sudo.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. BloodHound node info -> description interessante sur un compte.
2. mimikatz lsadump::dcsync /user:<compte> /history.
3. Login sur le serveur mail avec les creds historiques.
4. sudo bash -> root.

## Key Evidence

- dcsync /history produit un ancien hash/mot de passe exploitable.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
mimikatz lsadump::dcsync /history.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout (lecture visuelle verifiee).

## Reusable Lessons

- Toujours verifier les champs description BloodHound + dcsync /history pour recuperer d'anciens mots de passe reutilises ailleurs.

## Pattern Candidates

- Voir pattern associe de meme slug.
