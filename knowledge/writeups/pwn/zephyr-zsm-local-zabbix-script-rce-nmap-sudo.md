---
doc_kind: writeup
title: "Zephyr - zsm.local - RCE via scripts Zabbix admin + sudo nmap GTFOBins"
category: pwn
slug: zephyr-zsm-local-zabbix-script-rce-nmap-sudo
created: 2026-10-29
status: solved
tags:
  - zabbix
  - rce
  - sudo-nmap
  - gtfobins
  - privesc
source: "HTB Pro Lab Zephyr"
target: "Zabbix Server Linux"
---
# Zephyr - zsm.local - RCE via scripts Zabbix admin + sudo nmap GTFOBins

## Challenge Summary

- Source: HTB Pro Lab Zephyr
- Target: Zabbix Server Linux
- Goal: En tant qu'Admin Zabbix, creation d'un script malveillant execute sur le Zabbix Server lui-meme donnant un reverse shell; sudo nmap NOPASSWD permet la privesc root via script NSE.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Confirmer que le Zabbix Server est Linux.
2. Creer un script admin Zabbix (type webhook) avec payload curl/bash.
3. Executer via Monitoring->Hosts->Execute -> shell en tant que zabbix.
4. sudo -l revele nmap NOPASSWD.
5. nmap --script avec script NSE executant du code -> root.

## Key Evidence

- Shell zabbix obtenu; sudo -l confirme nmap NOPASSWD.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
Zabbix custom scripts (webhook type), bash reverse shell, nmap --script GTFOBins.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout (lecture visuelle verifiee).

## Reusable Lessons

- Zabbix Admin scripts = RCE natif; sudo nmap NOPASSWD = GTFOBins privesc classique.

## Pattern Candidates

- Voir pattern associe de meme slug.
