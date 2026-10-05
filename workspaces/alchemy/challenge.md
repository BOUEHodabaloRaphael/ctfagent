---
doc_kind: challenge
id: alchemy
title: Alchemy
category: pwn
platform: manual
platform_id: ""
url: 10.10.110.0/24
status: new
tags:
  []
attachments:
  []
---
# Alchemy

- ID: alchemy
- Category: pwn
- Platform: manual
- Platform ID: (not provided)
- URL: 10.10.110.0/24
- Attachments:
  - none

## Description

HTB Pro Lab: Alchemy LLC / Sogard Brewing Co. ICS/OT security assessment.

Scenario: IT/OT converged brewery environment. Objective: assess public IT interface, find misconfigurations allowing lateral movement into OT network, assess ability to disrupt brewery operations (PLCs/HMI) and steal IP. 21 flags total.

Rules of Engagement:
- No brute forcing or unreasonable guessing required; all info is documented/available in the lab.
- Do NOT fuzz the PLCs (OT side) - risk of instability/undefined behavior.

Known machines (from lab info page):
- ALCHEMY-FW (FreeBSD)
- ALCHEMY-WEB01 (Linux)
- ALCHEMY-LDAP (Windows)
- ALCHEMY-SCADA (Linux)
- ALCHEMY-WEB02 (Linux)
- ALCHEMY-WS01 (Windows)
- ALCHEMY-WS02 (Windows)
- ALCHEMY-EW (Windows)
- ALCHEMY-PRINTER (Linux)
- ALCHEMY-MASHMIXING-PLC (Other)
- ALCHEMY-LAUTERING-PLC (Other)
- ALCHEMY-BOILING-PLC (Other)
- ALCHEMY-COOLING-PLC (Other)
- ALCHEMY-FERMENTATION-PLC (Other)
- ALCHEMY-CONDITIONING-PLC (Other)
- ALCHEMY-BOTTLING-PLC (Other)

VPN: connected, tun0 10.10.14.71/23, lab entry subnet 10.10.110.0/24.

Flag categories hinted by names: Overfly, A New Beginning, Anxiety, What would you trade?, Digital prison panopticon, Vive la révolution de l'IA, Existential risk, What exactly is intelligent?, Is free will an illusion, We have never been modern, The denial of death, Amor Fati, Knowledge is power, Lost information, There is always another way, The secret is out!, The secret recipe.. Part 2, Who turned the heat up?!, The secret recipe.. Part 1, This didn't age well.., What a waste of good beer!

## Constraints

- No fuzzing PLCs/OT. Evidence-first: start with nmap sweep of 10.10.110.0/24, then service enum on discovered hosts, then web triage on ALCHEMY-WEB01/WEB02.
