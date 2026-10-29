---
doc_kind: writeup
title: "Endgame XEN - Ghost (pivot Metasploit + Kerberoast SPN legacy)"
category: misc
slug: xen-ghost-kerberoast-smb-pivot
created: 2026-10-29
status: solved
tags:
  - kerberoasting
  - metasploit-autoroute
  - hashcat-rules
  - smb-share
  - proxychains
source: "HTB Endgame XEN"
target: "Reseau interne 172.16.x via autoroute Metasploit"
---
# Endgame XEN - Ghost (pivot Metasploit + Kerberoast SPN legacy)

## Challenge Summary

- Source: HTB Endgame XEN
- Target: Reseau interne 172.16.x via autoroute Metasploit
- Goal: Pivot reseau via autoroute/socks4a Metasploit vers le sous-reseau interne, Kerberoasting d'un compte de service SQL avec SPN ancien, hash TGS casse avec hashcat+regles, acces SMB admin.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. post/multi/manage/autoroute ajoute la route vers le sous-reseau interne, socks4a en 1080.
2. proxychains GetUserSPNs.py avec creds existantes -> SPN de service SQL trouve.
3. hashcat -m 13100 avec une regle de mutation sur rockyou -> credential casse.
4. crackmapexec smb valide les creds, acces au partage admin.
5. Lecture directe du flag sur le partage.

## Key Evidence

- hashcat affiche "Status: Cracked" sur le hash $krb5tgs$23$*...

## Dead Ends

- n/a (see Reusable Lessons for pitfalls encountered)

## Payloads And Commands

```text
requete Kerberoast (GetUserSPNs.py) + crack hashcat mode 13100 avec regle de mutation.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Appliquer des regles de mutation hashcat (dive.rule) sur rockyou avant de conclure qu'un hash Kerberoast est non cassable; toujours Kerberoaster depuis le premier foothold meme limite avant de chercher un autre vecteur.

## Pattern Candidates

- Nouveau pattern: xen-ghost-kerberoast-smb-pivot
