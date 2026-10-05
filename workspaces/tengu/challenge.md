---
doc_kind: challenge
id: tengu
title: Tengu
category: web
platform: manual
platform_id: ""
url: 10.13.38.40
status: new
tags:
  []
attachments:
  []
---
# Tengu

- ID: tengu
- Category: web
- Platform: manual
- Platform ID: (not provided)
- URL: 10.13.38.40
- Attachments:
  - none

## Description

HTB Pro Lab: Tengu (EU Mini Pro Lab 1). Mixed Active Directory environment, Red Team Operator I difficulty.

Scenario: penetration test on a small AD scenario with typical real-world company vulnerabilities. 3 flags: Red, Impersonate, Tengu Master.

Entry point: 10.13.38.40 (single IP, not a /24 range like Alchemy).

Exposed skill areas: Active Directory attacks, pivoting into internal networks, MSSQL attacks, Kerberos attacks, DPAPI operations.

Known machines:
- TENGU-SQL (Windows)
- TENGU-NODERED (Linux)
- TENGU-DC (Windows)

Lesson carried over from Alchemy session: avoid aggressive '-p- --min-rate' full-port scans in one pass against unknown services - caused a service hang requiring lab redeploy. Use gentler --top-ports / -T2-T3 first pass, light manual verification before heavier scans.

## Constraints

- No brute forcing needed per general HTB Pro Lab conventions unless stated otherwise. Scan gently (top-ports first, moderate timing) - do not repeat the full -p- --min-rate 1000 mistake from Alchemy. Entry point is a single IP (10.13.38.40), not a /24 sweep.
