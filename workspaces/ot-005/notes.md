# OT#005 — "Grid Command Injection" (substation RTU, IEC 60870-5-104-inspired)

## Target
- `169.58.126.107:6004` — battleCTF/bugpwn, category `ot`, value=150 at creation (0/3 attempts
  used as of 2026-10-28).
- Briefing: https://otctf.pages.dev/ot-005-grid-command-injection/
- Protocol: "inspired by IEC 60870-5-104" (real telecontrol standard for transmission/distribution
  grid SCADA — the protocol actually used in the 2015/2016 Ukraine grid attacks, which were
  literally IEC-104 command-injection attacks: unauthorized SCADA commands sent to RTUs to trip
  breakers). Title "command injection" strongly suggests the vuln is: no origin/authentication
  check on control-direction commands, so any client can send a command that should only come
  from the legitimate master station.

## Status: not yet started (fresh, 2026-10-28)

## Prior-series lessons carried over (same CTF, same OT category)
- OT#002 (solved): custom binary protocol, no auth, the "safety device" (sync-check) was simply
  absent server-side — exploit was to trigger the dangerous real-world condition (out-of-phase
  breaker reclose) via otherwise-normal protocol calls, then read a previously-inert diagnostic
  opcode which only returns the flag AFTER the dangerous condition is achieved. Pattern: find the
  missing safety check, trigger the real hazardous condition properly (not just any malformed
  input), then a formerly-boring "read" op surfaces the flag.
- OT#003: blocked (separate HTTP/SSRF furnace-control surface, fully exhausted methods/body
  fields).
- OT#004: blocked (OPC-UA-style Browse/Read/Write, 100% content-invariant across 3 exhaustive
  rounds — custom simplified opcode framing, NOT the real OPC-UA binary wire format).
- Working hypothesis for OT#005: unlike OT#004 (simplified custom framing), IEC 60870-5-104 is a
  REAL, well-documented, publicly-specified protocol (unlike OPC-UA here, which was deliberately
  "inspired" but NOT the real wire format) — worth checking early whether this challenge actually
  implements the real IEC-104 APDU/ASDU wire format, since if so, standard tooling/references
  apply directly instead of blind opcode fuzzing.

## IEC 60870-5-104 quick reference (for calibration — verify against the live service, don't assume)
- Transport: TCP port 2404 normally (this challenge uses 6004 instead, expected for a CTF).
- APCI (Application Protocol Control Information) frame: starts with start byte `0x68`, then
  1-byte APDU length (length of everything AFTER the length byte), then 4 bytes of control fields.
  - **I-format** (information transfer, carries an ASDU): control field 1 even (bit0=0) — contains
    send/receive sequence numbers (15-bit each).
  - **S-format** (sequence-number supervisory, no ASDU): control field 1 = `0x01`, 1 byte seq info.
  - **U-format** (unnumbered control, e.g. STARTDT/STOPDT/TESTFR activation+confirmation):
    control field 1 bits — `STARTDT act=0x07`, `STARTDT con=0x0B`, `STOPDT act=0x13`,
    `STOPDT con=0x17`, `TESTFR act=0x43`, `TESTFR con=0x83`.
  - A real IEC-104 session normally starts with the master sending `STARTDT act`, slave replies
    `STARTDT con`, THEN I-frames (actual ASDUs) start flowing.
- ASDU (Application Service Data Unit, carried inside I-frames): `[TypeId:1][VSQ:1]
  [Cause of Transmission (COT):1][Common Address of ASDU (CA):2 LE][InfoObjectAddr:3 LE][data...]`.
  - Relevant TypeIds for "command injection" into a breaker-like RTU:
    - `C_SC_NA_1` (45) = Single command (on/off, 1 bit + qualifier) — classic breaker trip/close.
    - `C_DC_NA_1` (46) = Double command (2-bit state: 0=not permitted,1=off,2=on,3=not permitted).
    - `C_RC_NA_1` (47) = Regulating step command.
    - `C_SE_NA_1`/`C_SE_NB_1`/`C_SE_NC_1` (48-50) = Setpoint commands.
  - Cause of Transmission (COT) byte matters a lot for real IEC-104: `6`=activation (act),
    `7`=activation confirmation, `8`=deactivation, `9`=deactivation confirmation, `10`=activation
    termination, `20`=interrogated by station, etc. A real master uses COT=6 (act) when issuing a
    command; this is the field most likely relevant to an "injection" vuln (e.g. does the RTU
    check WHO sent it, or just accept ANY COT=6 single-command frame regardless of source?).

## Next steps (not yet executed)
1. Single careful connect + raw banner/first-bytes capture — does the server send anything
   unsolicited on connect (real IEC-104 slaves don't normally send anything until the master
   sends STARTDT act)?
2. Send a real `STARTDT act` U-frame (`68 04 07 00 00 00`) and see if a `STARTDT con` comes back —
   this alone will confirm/deny whether the real wire format is implemented at all (fast,
   cheap, decisive test, do this FIRST before any custom-opcode guessing like OT#004's dead end).
3. If STARTDT handshake works: send a General Interrogation (`C_IC_NA_1`, TypeId=100, COT=6) to
   enumerate what information objects/points exist, read their current values/addresses.
4. Look specifically for a single/double command point that maps to a breaker, and for any
   indication of an origin/source-address field that SHOULD gate who can issue COT=6 activation
   commands but doesn't (the actual "injection" vuln per the challenge title).
5. Space requests out — all 3 of this platform's other OT/PWN challenges tested earlier this
   session had real anti-scan cooldowns; assume this one might too until proven otherwise.

## Probe 1 result (2026-10-28, confirmed REAL IEC-104 wire format)
- Connected to `169.58.126.107:6004`. No unsolicited banner within 2s of connect (matches real
  IEC-104 slave behavior — slaves stay silent until master sends STARTDT act).
- Sent real `STARTDT act` U-frame `68 04 07 00 00 00`.
- Received `68 04 0b 00 00 00` = **STARTDT con**, byte-for-byte exactly as the real spec predicts.
- **Conclusion: this challenge implements the REAL IEC 60870-5-104 APCI framing**, unlike OT#004
  (which was a custom "inspired by OPC-UA" framing, NOT real OPC-UA binary). Standard protocol
  knowledge applies directly — proceeding with General Interrogation next instead of blind fuzzing.
- Script: `artifacts/probe1.py`, raw log: `artifacts/probe1.log`.

## Artifacts
- `artifacts/iec104.py` — early helper class (tx/rx seq packing needs re-check, superseded by
  per-probe scripts below which build frames explicitly).
- `artifacts/probe1.py` / `probe1.log` — STARTDT handshake confirmation.

## Anti-scan cooldown triggered (2026-10-28)
- After the successful probe1 handshake, a second connection attempt (`probe2.py`, General
  Interrogation on CA=1) made only ~a few seconds after probe1 closed got a dead connection: TCP
  connect succeeded instantly but every `recv()` returned empty (immediate EOF), including even
  the STARTDT response that had worked moments before.
- Waited 100s, retried with a single consolidated script (`probe3.py`: one persistent connection,
  banner capture + STARTDT + GI all paced ≥1.2s apart) — still fully dead (EOF on every recv,
  including STARTDT con this time). So the block from the second connection attempt persisted
  through the 100s wait (or was extended/retriggered).
- Consistent with this platform's known anti-scan cooldown (45-90s typical elsewhere, but here two
  connection attempts in quick succession seem to have triggered something that outlasted 100s).
- Action: waiting a longer interval (180s) before the next attempt, and from here on making only
  ONE connection per attempt, fully self-contained (handshake + GI + anything else needed), with
  generous pacing, to avoid re-triggering/extending the block.
- After the full 600s wait (≈900s cumulative since the block started), retried the same clean
  single-connection probe (`probe3.py`) again: still 100% dead — TCP connects instantly (0.1s) but
  every single `recv()` times out with zero bytes, including the previously-reliable STARTDT
  response. Confirmed independently of my Python socket code with raw `nc` (`printf ... | nc -w5
  169.58.126.107 6004`) — also silent. Confirmed the port itself is genuinely open and the host is
  up via `nmap -Pn -p 6004` (reports `open`, ~0.12-0.14s latency) — so this is an **application-
  layer** silence/block, not a network/firewall-level drop, and not a local artifact.
  **CAUTION: the two nmap probes used for this check are themselves a form of scanning and may
  have reset/extended the block further — avoiding any further nmap/scanning from here on, raw
  socket connects only.**
- Unlike OT#003 (needed ~600s, confirmed reliable there) and OT#004 ("45-90s typical", up to a few
  hundred seconds for a deliberately aggressive 256-opcode sweep), this block has now outlasted
  ~900s cumulative with no recovery. No per-instance "redeploy"/"spawn" option exists for this
  challenge on the platform (confirmed via `ctf_platform_client.py show-challenge --id 35`: no
  docker/instance controls, just a static connection_info string) — unlike HTB Pro Lab's
  "Unresponsive Machine" redeploy button, there is nothing to request here; waiting it out (or
  escalating to organizers) are the only options.
- Next: one more, longer (900s/15min) wait with absolutely no further scanning of any kind, then a
  single clean raw-socket attempt. If that also fails, treat this as blocked for this session and
  report back rather than continuing to guess/retry indefinitely.
- Did the 900s wait (no scanning, no reconnects during the wait). Retried the identical clean
  `probe3.py` single-connection probe once more: **still 100% dead** — TCP connect still succeeds
  instantly (0.11-0.13s, consistent across every attempt), but every `recv()` on STARTDT and GI
  times out with zero bytes. Cumulative elapsed time since the triggering event (second connection
  in probe2.py): ~100s + 180s + 600s + 900s of deliberate waits alone ≈ 30 minutes, plus script
  runtime/analysis time in between (closer to 35-40 min wall clock total).

## Status: BLOCKED (2026-10-28) — service unresponsive, cause ambiguous, no recovery after ~35-40min
- **What is confirmed:** this challenge DOES implement the real IEC 60870-5-104 APCI wire format.
  The very first-ever connection (`probe1.py`) sent a byte-exact real `STARTDT act` frame
  (`68 04 07 00 00 00`) and received a byte-exact real `STARTDT con` (`68 04 0b 00 00 00`) — this
  is strong, unambiguous evidence (unlike OT#004's fake-OPC-UA framing). The main briefed strategy
  (verify real protocol first) worked and paid off immediately.
- **What went wrong:** the very next connection attempt (sending a General Interrogation ASDU,
  `probe2.py`), made only a few seconds after the first connection closed, got no response at all
  (not even STARTDT con this time) — and the service has remained **fully silent on every
  subsequent attempt since**, through ~35-40 minutes of cumulative waiting (100s, 180s, 600s, 900s
  staged backoffs, matching and exceeding this platform's known cooldown patterns from OT#003
  (600s reliable) and OT#004 (45-90s typical, longer after aggressive scans)).
- **Two live hypotheses, not disambiguated:**
  1. An anti-scan/rate-limit block far longer-lived here than on sibling OT challenges (possibly
     because a malformed/unexpected ASDU in the GI frame — CA guessed as 1, QOI=20 — was flagged
     as hostile/fuzzing rather than a normal cooldown trigger).
  2. The GI frame crashed or wedged the actual IEC-104 server process, and the TCP accept the
     clients see now is from a load-balancer/proxy in front of a dead backend (would explain why
     waiting indefinitely doesn't help — nothing is "cooling down," the app is just gone). Nmap
     confirms the TCP port itself stays genuinely "open" throughout (`nmap -Pn -p 6004` → open,
     ~0.12s latency), consistent with either hypothesis.
- **Ruled out:** not a local/client-side issue (reproduced independently with plain `nc`, not just
  the Python socket code); not a firewall-level drop (TCP handshake always completes in ~0.1s).
- **No self-service redeploy exists** for this challenge on the platform — confirmed via
  `ctf_platform_client.py show-challenge --id 35`: static `connection_info` string, no per-user
  docker/instance controls (unlike HTB Pro Labs' "Unresponsive Machine" button). Waiting longer or
  asking organizers to restart the backend are the only remaining options.
- **No flag obtained. 0/3 platform attempts used** (as required, no submission was attempted).
- **If resuming later:** do NOT immediately repeat the GI frame that preceded the lockup. First do
  a single bare STARTDT-only probe (`probe1.py`, already proven safe/working once) to check if the
  service is back. Only after that succeeds, retry General Interrogation — but consider varying
  the CA (Common Address) value (tried only CA=1 so far; real IEC-104 CAs can be 1-65534, and an
  unexpected CA for this RTU might itself be rejected/ignored rather than crash — worth trying
  CA=0xFFFF broadcast too) and/or add a short delay/second GI attempt before concluding the
  response is truly empty, in case GI responses are just slow rather than crash-triggering.
- `artifacts/probe2.py` / `.log`, `artifacts/probe3.py` / `.log` — the two blocked attempts
  (both show empty/EOF responses).
- Retried probe3 again after the 180s wait (280s cumulative since the block) — still fully dead
  (no STARTDT con, no GI response at all; true timeouts, not just an empty-banner false positive —
  verified the `drain()` helper does capture data immediately when it arrives, as proven by
  probe1's successful capture using the same recv-based approach).
- Cross-referenced `workspaces/ot-003/notes.md`: that challenge's rate-limit needed a genuine
  **~600s idle wait** to reliably clear; 30s and 150s backoffs did NOT reliably clear it.
  `workspaces/ot-004/notes.md` reports a similar "extended lockout independent of retry timing"
  pattern. Recalibrating to a 600s wait before the next (single, final-shape) probe attempt.
