# OT#002 — Solve Notes

## Target
TCP `169.58.126.107:6001`, custom binary protocol, 5-byte requests, no auth.

## Protocol discovered (black-box)

Request frame: `[opcode:1][payload:4]` (payload mostly ignored/unused for commands found).

Valid opcodes (only 5 of 256 respond non-error):

| Opcode | Function | Normal response |
|---|---|---|
| `0x01` | Read telemetry | 11 bytes: `[status:1][grid_phase:f32 LE][gen_phase:f32 LE][trailer:2]` — phase angles in degrees, wrap mod 360 |
| `0x02` | TRIP (open breaker) | `0x00` (1 byte ack) |
| `0x03` | CLOSE breaker | `0x01` = normal close (in/near phase); `0x02` = **out-of-phase close** (destructive event) |
| `0x04` | Read flag/const (sync-check device presence) | `0x00` constant — confirms device 25 (sync-check) absent |
| `0x05` | Diagnostic/incident buffer | `0x01` (1 byte) normally; **after destructive close, returns 129-byte buffer containing the flag as ASCII, null-padded** |

Telemetry trailer byte 9 reflects breaker state: `00`=open, `01` at offset 9=closed-normal, offset 10 byte flips to `01` after destructive event (out-of-phase close), and grid/gen phase floats keep drifting independently post-event (generator no longer locked/synced — consistent with it tripping offline / being destroyed).

## Key finding

- Grid and generator phase angles (`op 0x01` floats) drift relative to each other when breaker is OPEN — slow "beat" cycle, differential periodically approaches ±180° (anti-phase) roughly every ~70s window observed.
- No sync-check (device 25) present server-side — `CLOSE` (`op 0x03`) is accepted regardless of phase differential (confirmed: briefing explicitly states no sync-check).
- Sending `CLOSE` while `|phase_grid - phase_gen| ≈ 175-180°` (anti-phase) produces response `0x02` instead of the normal `0x01` — this is the Aurora-style destructive out-of-phase reclose.
- After this event, opcode `0x05` (previously inert, always `0x01`) returns an extended buffer containing the flag in ASCII.

## Exploit sequence (reproducible, 3/3 runs identical)

1. Connect TCP to `169.58.126.107:6001`.
2. Do NOT close the breaker yet (stay in default OPEN state).
3. Poll `op 0x01` (telemetry) repeatedly (~every 150ms), decode `f1`/`f2` as little-endian floats (degrees), compute `norm(f1-f2)` (wrapped to [-180,180]).
4. When `abs(diff) > ~175`, immediately send `op 0x03` (CLOSE).
5. Server responds `0x02` (destructive out-of-phase reclose, vs normal `0x01`).
6. Send `op 0x05` — response is 129 bytes: `[status:1][ascii flag + null padding]`.
7. Strip leading status byte and trailing nulls, decode ASCII.

Script: `artifacts/aurora_trigger.py` (watch phase, trigger close). Full fuzz log: `artifacts/opcode_scan.log`, `artifacts/post_event_fuzz.log`.

## FLAG (verified 3x, stable/deterministic)

```
CTF{604dfaa5b5ec40f71a4d1b6690b6f433}
```

## Status
Solved, flag confirmed and SUBMITTED - platform returned "Correct" (1/3 attempts used).

FLAG VALIDATED: CTF{604dfaa5b5ec40f71a4d1b6690b6f433}
