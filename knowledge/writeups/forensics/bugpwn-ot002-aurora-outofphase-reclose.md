---
doc_kind: writeup
title: "battleCTF Qualifier (bugpwn) — OT#002 (Aurora-style out-of-phase breaker reclose, custom binary protocol)"
category: forensics
slug: bugpwn-ot002-aurora-outofphase-reclose
created: 2026-11-10
status: solved
tags:
  - ot-ics
  - aurora-vulnerability
  - custom-protocol
  - black-box-protocol-reversing
source: "ctf.bugpwn.com — battleCTF Qualifier 2026 (challenge id 26, ot, up to 45 pts)"
target: "169.58.126.107:6001 — custom binary protocol (5-byte requests), simulated grid-tie synchrophasor device"
---
# battleCTF Qualifier — OT#002

## Challenge Summary

- A TCP service speaking a small custom binary protocol (no auth), modeling a grid-tie breaker
  with synchrophasor-style telemetry — the goal is to trigger an **Aurora-style out-of-phase
  reclose** (the real-world 2007 DHS Aurora Generator Test attack class: closing a breaker while
  grid and generator phase are far apart, which destroys rotating equipment) to make the device
  dump a flag it normally never exposes.

## Initial Signals

- Request frame: `[opcode:1][payload:4]`, payload mostly unused for the opcodes that mattered.
- Only 5 of 256 possible opcodes respond non-error — fully black-box mapped by brute-scanning the
  opcode byte space:

  | Opcode | Function | Normal response |
  |---|---|---|
  | `0x01` | Read telemetry | 11 bytes: `[status][grid_phase f32 LE][gen_phase f32 LE][trailer:2]` |
  | `0x02` | TRIP (open breaker) | `0x00` ack |
  | `0x03` | CLOSE breaker | `0x01` normal close; `0x02` = **out-of-phase close** (destructive) |
  | `0x04` | Read sync-check device presence | constant `0x00` → confirms device 25 (sync-check) absent |
  | `0x05` | Diagnostic/incident buffer | `0x01` normally; **129-byte flag buffer after a destructive close** |

## Exploit Chain (reproducible, confirmed 3/3 runs identical)

1. Connect; leave the breaker in its default **open** state (never send `0x02`/`0x03` yet).
2. Poll `0x01` (telemetry) repeatedly (~every 150ms), decoding the two little-endian floats
   (grid phase, generator phase, both degrees) and computing `norm(phase_grid - phase_gen)`
   wrapped to `[-180, 180]`. With the breaker open, the two phases drift independently (no
   sync-check device present server-side to prevent it), slowly beating in and out of alignment,
   periodically approaching ±180° (anti-phase) roughly every ~70s window observed.
3. When `abs(diff) > ~175°` (near-maximal anti-phase), immediately send `0x03` (CLOSE). Because
   no sync-check device (`25`) exists on this simulated bus, the CLOSE is accepted regardless of
   phase differential — the server responds `0x02` instead of the normal `0x01`, confirming the
   destructive out-of-phase reclose fired.
4. Send `0x05` (diagnostic buffer) — now returns the extended 129-byte buffer:
   `[status:1][ascii flag + null padding]`. Strip the leading status byte and trailing nulls,
   decode as ASCII.

## Key Evidence

- Telemetry trailer byte 9 reflects breaker state directly (`00`=open, `01`=closed-normal); byte 10
  flips to `01` specifically after the destructive event, and the phase floats continue to drift
  independently post-event (generator no longer locked/synced — consistent with it having
  "tripped offline"/been destroyed in the simulated model), corroborating that `0x02` really is a
  distinct, destructive outcome rather than a protocol quirk.
- Full fuzz logs preserved: `workspaces/ot-002/artifacts/opcode_scan.log` (opcode space sweep),
  `workspaces/ot-002/artifacts/post_event_fuzz.log` (behavior after the destructive event).

## Payloads And Commands

Script: `workspaces/ot-002/artifacts/aurora_trigger.py` — watches the phase differential live and
fires the CLOSE at the anti-phase window automatically.

```python
# core loop shape
while True:
    status, grid_phase, gen_phase = read_telemetry(sock)   # opcode 0x01
    diff = normalize_deg(grid_phase - gen_phase)
    if abs(diff) > 175:
        send_close(sock)                                   # opcode 0x03
        break
flag_buf = read_diag_buffer(sock)                           # opcode 0x05
flag = flag_buf[1:].rstrip(b"\x00").decode()
```

## Flag / Outcome

- `CTF{604dfaa5b5ec40f71a4d1b6690b6f433}` — verified 3x stable/deterministic across repeat runs,
  submitted and confirmed correct (1 of 3 allowed attempts used).

## Reusable Lessons

- For an unknown custom binary protocol on an OT/ICS-themed challenge, a full opcode-byte sweep
  (all 256 values of the first frame byte) is a cheap, fast way to black-box map the entire
  command surface before reasoning about semantics — only a handful of opcodes usually respond
  non-error, narrowing the real investigation quickly.
- Recognize real-world ICS attack classes (Aurora out-of-phase reclose, Stuxnet-style setpoint
  manipulation, Oldsmar-style chemical dosing) from the challenge's flavor text — they map directly
  onto a specific sequence of protocol operations to try, rather than needing to be discovered by
  blind fuzzing.
- A device whose absence is explicitly confirmable via its own protocol (`0x04` here, "sync-check
  device not present") is a strong, direct signal that the corresponding safety check is not
  enforced server-side — worth checking for this kind of "is the guard even installed" probe
  before assuming a destructive action will be blocked.

## Related

- [`bugpwn-ot001-modbus-static-flag`](bugpwn-ot001-modbus-static-flag.md) — the other OT challenge
  on this same platform, with a less clean end-to-end confirmation (sourced writeup vs. live
  register state mismatch) compared to this fully self-reproduced chain.
- [`ics-scada-protocol-hierarchy-triage`](../../patterns/forensics/ics-scada-protocol-hierarchy-triage.md) —
  general ICS/SCADA protocol-triage pattern in this knowledge base.
