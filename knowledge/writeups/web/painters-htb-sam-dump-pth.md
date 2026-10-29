---
doc_kind: writeup
title: "Zephyr - Painters.htb - mimikatz lsadump::sam + pass-the-hash"
category: web
slug: painters-htb-sam-dump-pth
created: 2026-10-29
status: solved
tags:
  - pass-the-hash
  - mimikatz
  - lsadump
  - lateral-movement
source: "HTB Pro Lab Zephyr"
target: "Machine SYSTEM via psexec"
---
# Zephyr - Painters.htb - mimikatz lsadump::sam + pass-the-hash

## Challenge Summary

- Source: HTB Pro Lab Zephyr
- Target: Machine SYSTEM via psexec
- Goal: Sur une machine deja SYSTEM, mimikatz dump le SAM local et recupere un hash NTLM, utilise en pass-the-hash sur une autre machine interne.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Upload mimikatz+nc.
2. lsadump::sam -> hash d'un utilisateur local.
3. cme smb hash spray sur les machines internes -> succes.
4. psexec.py avec le hash -> SYSTEM.

## Key Evidence

- Sortie mimikatz du dump SAM local.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
mimikatz lsadump::sam, crackmapexec, psexec.py -hashes.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout (lecture visuelle verifiee).

## Reusable Lessons

- Dump SAM local puis pass-the-hash est un pattern standard de mouvement lateral post-SYSTEM.

## Pattern Candidates

- Voir pattern associe de meme slug.
