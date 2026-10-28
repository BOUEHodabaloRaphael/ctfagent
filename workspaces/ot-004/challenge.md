---
doc_kind: challenge
id: ot-004
title: "OT#004"
category: ot
platform: manual
platform_id: ""
url: 169.58.126.107:6003
status: new
tags:
  []
attachments:
  []
---
# OT#004

- ID: ot-004
- Category: ot
- Platform: manual
- Platform ID: (not provided)
- URL: 169.58.126.107:6003
- Attachments:
  - none

## Description

This is a chemical reactor's process control interface, speaking an
OPC-UA-inspired protocol: a session handshake, then Browse/Read/Write
against a small address space of numbered nodes, the same client-facing
model real OPC-UA servers use to expose both process data and safety
systems side by side.

The reactor has an independent safety system that is supposed to stop
a runaway condition regardless of what the process controller is
doing. Find a way to make that protection not apply.

Reference: https://otctf.pages.dev/ot-004-chemical-reactor/

Connection: 169.58.126.107 6003

## Constraints

- Platform: bugpwn.com (ctf.bugpwn.com), challenge id=33, 150->decaying pts, max_attempts=3, solves so far=2. OPC-UA-inspired custom protocol. Reference writeup page: https://otctf.pages.dev/ot-004-chemical-reactor/ (part of a series: OT#001/002/003 already in workspaces/ot-002, ot-003).
