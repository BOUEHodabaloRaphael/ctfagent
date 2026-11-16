---
doc_kind: challenge
id: thundercipher-tc-vapt-exam
title: "ThunderCipher TC-VAPT Exam"
category: web
platform: manual
platform_id: ""
url: ""
status: new
tags:
  []
attachments:
  []
---
# ThunderCipher TC-VAPT Exam

- ID: thundercipher-tc-vapt-exam
- Category: web
- Platform: manual
- Platform ID: (not provided)
- URL: (not provided)
- Attachments:
  - none

## Description

TC-VAPT exam, exam/1 on thundercipher.in. 3 targets (all ssh+http only), VPN 10.8.0.57/tun0 connected via /home/kali/ctf/thundercipher/thundercipher-vpn.ovpn.

- Vault: 192.168.5.249, 120pts. 'internal vault system believed secure, recent audits suggest possible exposure of sensitive configuration data.'
- UploadX: 192.168.5.119, 160pts. 'file-sharing platform, improper input validation mechanisms' (file upload).
- Phantom: 192.168.5.237, 180pts. 'suspicious activity detected, investigate if attacker established persistence' (forensics/post-exploitation).

Objective: initial access + root on every machine, capture user+root flags format ThunderCipher{...}. 12h lab timer, 24h report window after. Report PDF to reports@thundercipher.in.

## Constraints

- Evidence-first: nmap/httpx/source read before exploitation. 12h hard timer - prioritize Vault (lowest pts/likely easiest) first.
