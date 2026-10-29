---
doc_kind: writeup
title: "Zephyr - zsm.local - DB password reuse + hashcat + Chrome creds dump"
category: web
slug: zephyr-zsm-local-db-creds-chrome-dump
created: 2026-10-29
status: solved
tags:
  - credential-reuse
  - chrome-dump
  - hashcat
  - enum-chrome
source: "HTB Pro Lab Zephyr"
target: "Zabbix DB + machine Windows avec Chrome"
---
# Zephyr - zsm.local - DB password reuse + hashcat + Chrome creds dump

## Challenge Summary

- Source: HTB Pro Lab Zephyr
- Target: Zabbix DB + machine Windows avec Chrome
- Goal: Un fichier de config revele le mot de passe DB; dump de la table users; hashcat casse un hash bcrypt. Un dump Chrome extrait ensuite des creds stockes utiles plus loin dans le lab.

## Initial Signals

- Entry point: see Exploit Chain step 1
- Visible hints: n/a (see source writeup)
- First confirming probe: see Exploit Chain

## Exploit Chain

1. Lecture du fichier de config -> mot de passe DB.
2. mysql dump table users -> hash bcrypt.
3. hashcat -m 3200 avec rockyou -> mot de passe.
4. Pivot meterpreter+autoroute+socks_proxy.
5. winPEAS trouve un chemin Chrome passwords.
6. post/windows/gather/enum_chrome dump des creds Chrome utiles plus loin dans le lab.

## Key Evidence

- hashcat confirme le crack bcrypt; enum_chrome affiche les creds dechiffres avec l'URL associee.

## Dead Ends

- n/a (see Reusable Lessons)

## Payloads And Commands

```text
hashcat -m 3200, post/windows/gather/enum_chrome, winPEAS.bat.
```

## Flag / Outcome

- Flag obtenu, chaine confirmee de bout en bout (lecture visuelle verifiee).

## Reusable Lessons

- Les fichiers de config applicatifs contiennent souvent des mots de passe reutilises; dump Chrome via module metasploit tres efficace pour recuperer des creds stockes.

## Pattern Candidates

- Voir pattern associe de meme slug.
