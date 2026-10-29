---
doc_kind: writeup
title: "P.O.O. - PrivEsc (bypass firewall IPv4 via IPv6 vers WinRM)"
category: misc
slug: poo-privesc-ipv6-firewall-bypass-winrm
created: 2026-10-29
status: solved
tags:
  - ipv6-bypass
  - firewall-evasion
  - winrm
  - dual-stack
  - nmap-6
source: "HTB Mini Pro Lab P.O.O."
target: "Hote dual-stack IPv4/IPv6"
---
# P.O.O. - PrivEsc (bypass firewall IPv4 via IPv6 vers WinRM)

## Challenge Summary

- Source: HTB Mini Pro Lab P.O.O.
- Target: Hote dual-stack IPv4/IPv6
- Goal: Le port WinRM (5985) est filtre en IPv4 mais ouvert sans restriction sur l'adresse IPv6 publique de la meme machine, permettant une connexion WinRM directe avec des creds admin local deja obtenues.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Depuis un contexte limite, ipconfig revele une adresse IPv6 publique.
2. nmap -6 -p 5985 sur cette adresse -> port ouvert (alors que filtre en IPv4).
3. Ajout d'une entree /etc/hosts associant le FQDN connu a l'IPv6.
4. evil-winrm vers ce FQDN avec les creds admin local -> shell admin.

## Key Evidence

- nmap -6 -p 5985 affiche le port ouvert alors que le scan IPv4 initial ne le montrait pas.

## Dead Ends

- n/a (see Reusable Lessons for pitfalls encountered)

## Payloads And Commands

```text
scan et connexion directe sur adresse IPv6.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout.

## Reusable Lessons

- Un scan TCP IPv4 filtre n'est jamais une preuve qu'un service est absent; si la cible a une adresse IPv6, toujours rescanner les ports consideres fermes en -6.

## Pattern Candidates

- Nouveau pattern: poo-privesc-ipv6-firewall-bypass-winrm
