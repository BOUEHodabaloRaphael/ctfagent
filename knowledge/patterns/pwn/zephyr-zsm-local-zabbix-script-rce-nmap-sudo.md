---
doc_kind: pattern
title: "Zephyr - zsm.local - RCE via scripts Zabbix admin + sudo nmap GTFOBins"
category: pwn
slug: zephyr-zsm-local-zabbix-script-rce-nmap-sudo
created: 2026-10-29
status: active
tags:
  - zabbix
  - rce
  - sudo-nmap
  - gtfobins
  - privesc
chain_summary: "En tant qu'Admin Zabbix, creation d'un script malveillant execute sur le Zabbix Server lui-meme donnant un reverse shell; sudo nmap NOPASSWD permet la privesc root via script NSE."
---
# Zephyr - zsm.local - RCE via scripts Zabbix admin + sudo nmap GTFOBins

## Chain Summary

- One-line chain: En tant qu'Admin Zabbix, creation d'un script malveillant execute sur le Zabbix Server lui-meme donnant un reverse shell; sudo nmap NOPASSWD permet la privesc root via script NSE.

## Preconditions

- Voir le writeup associe pour le contexte precis de la cible.

## Cheap Probes

- Rechercher les signaux initiaux decrits dans la chaine d'exploit ci-dessous.

## Telltale Evidence

- Shell zabbix obtenu; sudo -l confirme nmap NOPASSWD.

## Escalation Order

1. Confirmer que le Zabbix Server est Linux.
2. Creer un script admin Zabbix (type webhook) avec payload curl/bash.
3. Executer via Monitoring->Hosts->Execute -> shell en tant que zabbix.
4. sudo -l revele nmap NOPASSWD.
5. nmap --script avec script NSE executant du code -> root.

## Common Mistakes

- Ne pas verifier ce signal/cette condition avant de passer a une autre piste.

## Payload Shapes

```text
Zabbix Admin scripts = RCE natif; sudo nmap NOPASSWD = GTFOBins privesc classique.
```

## Related Writeups

- zephyr-zsm-local-zabbix-script-rce-nmap-sudo

## Skill Impact

- Related skill: a classer lors d'une prochaine passe skill-maintainer si le pattern se repete.
- Rule to add or update: (backlog only for now; promote if this pattern repeats)
