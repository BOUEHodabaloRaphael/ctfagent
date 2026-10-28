---
doc_kind: challenge
id: ot-002
title: "OT#002"
category: ot
platform: manual
platform_id: ""
url: 169.58.126.107:6001
status: new
tags:
  []
attachments:
  []
---
# OT#002

- ID: ot-002
- Category: ot
- Platform: manual
- Platform ID: (not provided)
- URL: 169.58.126.107:6001
- Attachments:
  - none

## Description

This is direct network access to a substation's generator breaker controller. It speaks a small custom binary TCP protocol, with no protocol documentation, no source, and no binary provided. Discover it by talking to it.

Reference link: https://otctf.pages.dev/ot-002-substation-breaker/

--- Briefing page (otctf.pages.dev) ---
ASSET BKR-52 / FEEDER GEN-1 TIE / LINK CUSTOM TCP
BREAKER 52 FIELD BRIEFING

Generator tie breaker at the grid interconnection point. Controller reachable directly over the plant network, small custom binary protocol.

OT-002 · SUBSTATION-BREAKER, CATEGORY: OT

ACCESS PATH & INTERCONNECTION: CLIENT -> BREAKER CTRL (TCP :6001, 5-byte cmds) -> BREAKER 52 -> GRID BUS / GENERATOR
DEVICE 25 (sync-check relay) NOT PRESENT HERE.
Device numbers follow ANSI/IEEE C37.2 convention (52 = AC circuit breaker, 25 = synchronizing check).
Command bytes, response formats and any numeric thresholds are not published: discover them by talking to the endpoint.

PHASE RELATIONSHIP: grid vs generator, schematic only, phase angle delta between grid and generator.

CONNECTION:
TARGET: TARGET_HOST:6001
PROTOCOL: Custom binary, 5-byte requests
AUTHENTICATION: NONE
SYNC-CHECK (DEV. 25): NOT PRESENT

FIELD INCIDENT LOG - MAR 2007 - IDAHO NATIONAL LAB
The Aurora Generator Test: a test generator was remotely reclosed onto the grid while out of phase, producing a sudden torque transient severe enough to physically destroy it, using only an ordinary breaker command.

OBJECTIVE: Physically destroy the generator, then retrieve the flag that records the incident.
FORMAT: CTF{...}
NO SOURCE, NO BINARY, NO PROTOCOL DOC PROVIDED
NO MEMORY-CORRUPTION BUG INVOLVED

## Constraints

- Platform shows 0/3 attempts remaining for flag submission - be careful, do not guess-submit.
- No source, no binary, no protocol doc - protocol must be discovered by black-box probing of the TCP service.
- No memory-corruption bug involved (explicitly stated).
- Goal is logical: replicate Aurora Generator Test (out-of-phase reclose) via the custom 5-byte binary protocol.
