---
doc_kind: writeup
title: "Zephyr - Painters.htb - Kerberoasting + psexec SYSTEM"
category: web
slug: painters-htb-kerberoast-web-svc
created: 2026-10-29
status: solved
tags:
  - ad
  - kerberoasting
  - bloodhound
  - psexec
source: "HTB Pro Lab Zephyr"
target: "AD painters.htb, compte de service kerberoastable"
---
# Zephyr - Painters.htb - Kerberoasting + psexec SYSTEM

## Challenge Summary

- Source: HTB Pro Lab Zephyr
- Target: AD painters.htb, compte de service kerberoastable
- Goal: BloodHound identifie des comptes kerberoastables; GetUserSPNs.py extrait les TGS; hashcat casse le hash du compte de service; psexec reutilise le hash obtenu.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Upload SharpHound.exe, collecte BloodHound.
2. GetUserSPNs.py extrait le hash TGS du compte de service.
3. hashcat -m 13100 -> mot de passe.
4. psexec.py sur la machine cible.

## Key Evidence

- hashcat confirme le crack; psexec donne un shell SYSTEM.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
SharpHound, GetUserSPNs.py, hashcat -m 13100, psexec.py.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout (lecture visuelle verifiee).

## Reusable Lessons

- Kerberoasting classique: toujours collecter BloodHound tot pour identifier les comptes avec SPN.

## Pattern Candidates

- Voir pattern associe de meme slug.
