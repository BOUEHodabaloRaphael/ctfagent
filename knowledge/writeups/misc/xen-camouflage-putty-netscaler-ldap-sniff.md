---
doc_kind: writeup
title: "Endgame XEN - Camouflage (crack PuTTY + SSH NetScaler + sniff LDAP)"
category: misc
slug: xen-camouflage-putty-netscaler-ldap-sniff
created: 2026-10-29
status: solved
tags:
  - putty-crack
  - kwprocessor
  - netscaler
  - ldap-cleartext
  - tcpdump
source: "HTB Endgame XEN"
target: "Cle privee PuTTY + appliance NetScaler"
---
# Endgame XEN - Camouflage (crack PuTTY + SSH NetScaler + sniff LDAP)

## Challenge Summary

- Source: HTB Endgame XEN
- Target: Cle privee PuTTY + appliance NetScaler
- Goal: Craquage d'une cle privee PuTTY protegee par passphrase via wordlist kwprocessor (keyboard walks) plutot que rockyou, acces shell NetScaler, puis capture reseau tcpdump exposant un flag HTTP et des creds LDAP en clair.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. putty2john convertit private.ppk, john avec wordlist kwprocessor casse la passphrase.
2. puttygen convertit la cle en format OpenSSH.
3. SSH vers NetScaler via proxychains, shell CLI -> shell Unix sous-jacent.
4. tcpdump filtre pour capturer le trafic transitant par le NetScaler.
5. Analyse Wireshark: flag HTTP en clair + creds de service en clair sur LDAP (port 389).

## Key Evidence

- john affiche "1g 0:00:00:00 DONE" avec la passphrase recuperee.

## Dead Ends

- n/a (see Reusable Lessons for pitfalls encountered)

## Payloads And Commands

```text
wordlist ciblee (kwprocessor keyboard-walks) au lieu d'une wordlist generique.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Pour une passphrase probablement keyboard walk, generer une wordlist dediee avec kwprocessor donne de meilleurs resultats que rockyou; un appliance reseau (NetScaler) en position MITM naturel merite un sniff de son trafic transitant (LDAP/HTTP en clair).

## Pattern Candidates

- Nouveau pattern: xen-camouflage-putty-netscaler-ldap-sniff
