---
doc_kind: challenge
id: komisergio-bassar-boot2root-pwn
title: "komisergio-bassar (boot2root pwn)"
category: pwn
platform: manual
platform_id: ""
url: 10.100.16.100:9999
status: new
tags:
  []
attachments:
  - attachments/script.py
---
# komisergio-bassar (boot2root pwn)

- ID: komisergio-bassar-boot2root-pwn
- Category: pwn
- Platform: manual
- Platform ID: (not provided)
- URL: 10.100.16.100:9999
- Attachments:
  - attachments/script.py

## Description

Boot2root/pwn challenge by creator komisergio, Bassar-themed (distinct from the komisergio-kpalime AD/ADCS challenge targeting 10.10.20.30). Target 10.100.16.100:9999, reachable via the team VPN nctf-vpn (AllowedIPs 10.100.16.0/24, handshake fresh). User supplied a pwn exploit stub (script.py) that talks to the service, sends a DEBUG command, parses a leak 'userpass @ 0xADDR shell @ 0xADDR' from the banner, then sends a padded ret-to-shell payload (offset 40, p64(shell)[:6]) -- classic stack buffer overflow / leak-based ret2win pattern.

## Constraints

- none
