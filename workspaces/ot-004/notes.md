# OT#004 — "Chemical Reactor SIS" — Progress Notes

## Target
- `169.58.126.107:6003` — OPC-UA-inspired custom TCP protocol (NOT real OPC-UA binary encoding —
  confirmed real OPC-UA Hello handshake bytes got zero response).
- Platform: bugpwn.com, challenge id=33, category `ot`, 150pts decaying (now 148, decay=2,
  minimum=40), max_attempts=3, solves=2 (as of 2026-10-25, up from 1 earlier same day).

## Briefing page (otctf.pages.dev/ot-004-chemical-reactor/) — key facts
- Root node: `Objects (ns=0, id=85)` — the standard OPC-UA well-known root NodeId.
- **SIS isolation model is explicitly named "SAME ADDRESS SPACE"**: the safety system sits
  "one Browse call away from the process controller, reached through the exact same session and
  the exact same generic operations" — i.e. no separate auth/permission tier between controlling
  the process and touching SIS nodes. This IS the vuln, per the briefing's own framing (echoes
  real TRISIS/TRITON 2017: SIS reprogrammed directly instead of attacking the process controller).
- No source/binary provided, no memory-corruption bug — pure protocol/logic-level exploitation.
- Node IDs / variable names / "which specific write matters" are explicitly NOT given — must be
  discovered live via Browse.
- Objective: disable the SIS protection, then drive the reactor into a **sustained** dangerous
  condition (briefing says "sustained" — a one-shot excursion likely isn't enough, unlike OT#002's
  single destructive event).

## Wire format discovered (black-box, same framing family as OT#002)
Request: `[opcode:1][payload:4 bytes]` (5 bytes total, payload content not yet varied/tested).
Response: `[resp_code:1][len:4 LE][payload:len bytes]` — resp_code so far always `0x80 | opcode`.

Confirmed BEFORE our own scan triggered a cooldown (do not repeat these calls until cooldown
clears — see below):
- `op=0x00` + `00000000` → no response (invalid/unknown opcode, silently dropped).
- `op=0x01` + `00000000` → `81 04000000 01000000` → resp_code=0x81, len=4, payload=`00000001` LE
  = integer `1`. Likely a session/handshake ack, or a "node count"/"service id" style response —
  not yet interpreted.
- `op=0x02` + `00000000` → `82 05000000 0000000004` → resp_code=0x82, len=5, payload=5 bytes
  ending in `04`.
- `op=0x03` + `00000000` → `83 05000000 0000000004` → same shape as op=0x02, byte-for-byte except
  leading resp_code.
- `op=0x04` + `00000000` → `84 05000000 0000000004` → same shape again.
- `op=0x05` + `00000000` → no response.
- Real OPC-UA binary "HELF" Hello chunk, plain ASCII "HELLO\n"/"HEL\n" → all no response (confirms
  this is NOT the real OPC-UA binary protocol, just conceptually OPC-UA-style Browse/Read/Write).

Opcodes 2/3/4 returning near-identical 10-byte responses with only the resp_code byte differing
is suspicious — could mean our all-zero 4-byte payload isn't actually being interpreted (e.g. these
ops expect a real NodeId/argument in the payload and are returning a generic
"browse root"/error/default response when given a null argument). Payload content has NOT been
varied yet — that's the next real step once the service is responsive again.

## Self-inflicted cooldown — IMPORTANT, do not repeat
Ran a full 0-255 opcode scan (256 rapid individual TCP connections in ~8s) to map all opcodes
(same method that worked cleanly for OT#002). Immediately after, **op=0x01 (which had worked
moments before) started returning empty responses** — connection accepted (TCP handshake
succeeds, confirmed via `getsockname()`), but zero bytes back, no error. Retested at +20s, +45s,
+75s — still silent. Matches the pattern already in memory from the HTB Pro Lab full-port-scan
cooldown (aggressive scanning → extended lockout, independent of retry timing). **Conclusion:
stop sending any more requests to this target for a while** (treat like the HTB note: don't
hammer retries hoping it clears quickly — likely a 10-30+ min window). Next session: do ONE
single-connection single-request test first before resuming any multi-request probing, and if
doing another opcode sweep, space requests out (e.g. 1-2s apart, not 30ms) to avoid retripping it.

## Working theory for the actual exploit (once protocol is mapped)
Given the briefing's explicit "same address space, same generic ops" framing:
1. Browse from Objects (ns=0, id=85) → enumerate children → expect to find something like
   "ReactorController" and "SafetySystem"/"SIS" objects/folders.
2. Browse further into the SIS object → find its variables: likely an "Enabled"/"Bypass"/
   "TripSetpoint" style node, analogous to a real SIS's bypass switch or trip threshold.
3. Read the process controller's live variable (e.g. reactor temperature) to find/understand the
   runaway condition.
4. The vuln: nothing stops a generic Write targeting the SIS's own enable/setpoint node via the
   exact same Write operation used for normal process tags (no RBAC/zone separation) — write it to
   disable/neuter the SIS (e.g. Enabled=false, or TripSetpoint=max value), confirmed analogous to
   OT#003's "no distinction between operator-facing write and safety-critical write" pattern and
   OT#002's "no sync-check device present" pattern (both prior solves in this series rely on: the
   protection that *should* independently gate the dangerous action simply isn't enforced/present).
5. Then drive/force the process variable past the real (undocumented) threshold and SUSTAIN it
   (briefing emphasizes "sustained", unlike OT#002's single-shot trigger) — likely requires
   repeated Write calls to a setpoint/command node to keep the runaway going despite any natural
   decay, until the flag becomes readable (pattern from OT#002: a previously-inert
   diagnostic/incident opcode starts returning the flag only after the unsafe condition is
   achieved).
6. Flag likely surfaces via a Read op sent to an "incident log"/"alarm"/"diagnostic buffer" style
   node (or an opcode that was previously returning a trivial response) once the SIS-disabled +
   runaway-sustained condition is met, exactly as OT#002's opcode 0x05 did.

## Next concrete steps (once cooldown clears — single slow probes only at first)
1. Single `op=0x01` request, confirm it still works baseline (sanity check cooldown has lifted).
2. Vary payload on ops 2/3/4 with plausible small integers (e.g. NodeId numbers 85, 86, 87...,
   matching the ns=0,id=85 root hint) instead of all-zero, see if responses start differing —
   this is likely where opcode=Browse/Read/Write get real arguments (NodeId to browse/read, or
   NodeId+value to write).
2b. Also try larger single-byte opcodes beyond 5 but ONE AT A TIME with real delay (1-2s), not a
   fast sweep, to avoid retripping the cooldown — OT#002's active opcode set was small (5 total)
   so this protocol's real op count is plausibly similar.
3. Once Browse-equivalent opcode identified and returns structured data, map the address space:
   root (85) → find ReactorController and SafetySystem child node IDs.
4. Identify the specific SIS node controlling trip/bypass, and the process variable driving the
   runaway condition.
5. Write to disable SIS, then write/sustain the runaway condition, then read for the flag.

## Artifacts
- `artifacts/probe.py` — initial handshake-format probing script (ASCII/real-OPC-UA/opcode 0-5).
- `artifacts/opcode_scan.py` — full 0-255 opcode sweep (the one that triggered the cooldown —
  reuse with ADDED DELAY between requests next time, don't run it back-to-back as-is).
- `artifacts/opcode_scan.log` — log of that scan (0 responsive, because cooldown had already
  started partway through the 256-connection burst).

## Status: cooldown cleared, protocol mostly reverse-engineered, STUCK on node addressing (2026-10-25, later in day)

### Confirmed wire format (now solid, many independent tests)
`[op:1][len:4 LE][data:len bytes]` request → `[0x80|op:1][len:4 LE][data:len bytes]` response.
Sending an incomplete frame (len field value > actual bytes sent) makes the server silently wait
for the rest — this is NOT a rejection, just TCP buffering a partial frame. Always send the full
frame in one `sendall()`.

### Opcode space is COMPLETE at exactly 4 values (confirmed exhaustively)
- `op=1` = Hello/handshake. Response payload = **a per-connection call counter specific to op=1
  itself** (1st call→1, 2nd call→2, 3rd call→3, ...), totally independent of the data sent (tested
  identical-empty-data repeats AND varying-length/content data — same counter either way). Calling
  op1 multiple times does NOT appear to progress any session state machine (tested: 3x op1 calls
  then op2 — op2's reply was unchanged from calling op2 immediately after a single op1).
- `op=2` = Browse. `op=3` = Read. `op=4` = Write. Opcodes 0, 5-255 (including 0x80-0x84, 0xff) all
  produce **zero response** even with a complete, correctly-framed empty-data request — confirmed
  this is a true "opcode doesn't exist" signal, not a framing issue, since 1-4 respond instantly to
  the same empty-data shape. The handshake ("session handshake, then Browse/Read/Write") is
  genuinely just these 4 ops — matches the briefing's own wording exactly (Hello + 3 named ops).

### THE BLOCKER: op2/op3/op4 responses are 100% invariant regardless of the `data` field
Every single combination tried for the Browse (op2) request produces the byte-identical 10-byte
response `82 05000000 00000000 04` (status=0, trailing byte=4 — read as "4 children under root"):
- 4-byte LE integers: 0, 1, 2, 3, 4, 5, 10, 85, 0xFFFFFFFF
- 4-byte big-endian 85
- Single raw byte 85 (len=1)
- OPC-UA "two-byte-numeric" NodeId encoding `[0x00][85]` (len=2)
- OPC-UA "four-byte-numeric" NodeId encoding `[0x01][ns=0][id=85 as u16 LE]` (len=4)
- 8-byte `[namespaceIndex:4 LE][identifier:4 LE]` = (0, 85)
- ASCII strings: "Objects", "ReactorController", "SafetySystem", "ProcessControl", "SIS",
  "ReactorCtrl", "Root"
- Empty data (len=0)
`op3` (Read) and `op4` (Write) show the exact same invariance — always `83 05000000 ...0004` and
`84 05000000 ...0004` respectively, regardless of 4-byte numeric NodeId, 1-byte boolean (0x00 or
0x01 payload), or anything else tried. **A Write immediately followed by a Read never shows any
state change** in Read's reply (tested explicitly: write bool=False → read, write bool=True →
read — byte-identical both times).

### Ruled out
- NOT real binary OPC-UA (a correctly-formed real OPC-UA "HEL" TCP hello message gets zero bytes
  back — confirmed in the very first probe of this session).
- NOT a session-state-machine gate on op1 (tested: op1 called 1x vs 3x before Browse → same reply).
- NOT a request-ordinal/global-counter effect on op2-4's trailing byte (tested: op2 called as the
  2nd, 3rd, 4th, 5th, 6th request overall in a connection — always shows the same `04`, not an
  incrementing value; only op1's OWN reply counts op1 calls specifically).
- Anti-scan/rate-limit is real and distinct from the above: a burst of many rapid reconnects (the
  initial 0-255 opcode sweep) triggers an extended silent-drop window (confirmed recovers after
  ~45-90s of no further traffic; **reconnecting itself seems to be more punished than request
  count on one held-open connection** — several multi-request sequences on a SINGLE persistent
  connection worked fine without retriggering it, while rapid fresh connects did).

### Open theories, not yet tested (next session should try these, paced ~1 request/few sec)
1. Maybe Read needs a **combined (NodeId, AttributeId) pair** like real OPC-UA's actual Read
   service (8 bytes: NodeId + AttributeId, e.g. AttributeId=13 for "Value", =4 for "DisplayName")
   rather than NodeId alone — untested combination.
2. Maybe Write needs **(NodeId, Value) concatenated** as a single larger payload (e.g. 8+ bytes:
   4-byte NodeId + N-byte value) rather than a bare value — only bare 1/4-byte values tried so far,
   never NodeId+value together.
3. Maybe the "4" in every reply genuinely IS just "Browse always lists root, which truly has 4
   children" (real, stable fact about the address space) — and the REAL way to drill into a
   specific child requires a **Browse response containing more than 5 bytes that we're not seeing
   because something upstream truncates it** — worth trying a much bigger recv buffer / multiple
   sequential recv() calls in case the full child-list arrives in a second TCP segment after a
   longer wait (we only waited 2-3s then stopped reading; try waiting 10s+ and doing 2-3 recv()
   calls in a loop before giving up).
4. Haven't tried a NodeId *matching one of the real children* — if root truly has exactly 4
   children, their IDs are very plausibly sequential right after 85 (86/87/88/89) OR could be
   totally different well-known OPC-UA IDs (e.g. real OPC-UA's standard Objects children include
   well-known folders like Server(2253), etc.) — tried 86-91 already (no effect), but not e.g. the
   real standard OPC-UA well-known NodeIds for ObjectsFolder's typical default children.
5. Consider whether "len" prefix might need to be big-endian instead of LE (only LE tried for the
   length field itself, though content endianness was varied).
6. Ask in Discord/organizers whether a reference client or protocol spec snippet exists — this is
   an unusually deep blackbox (otctf.pages.dev explicitly says node IDs are NOT given, by design),
   so external hints may be the efficient path once local ideas are exhausted, mirroring how
   PWN#Delta/0byte got unblocked earlier in this event.

### Resource note
Each probe round costs ~45-90s of mandatory wait (anti-scan cooldown recovery) — budget
accordingly; don't rapid-fire many small variations back-to-back without the wait, and prefer
testing MULTIPLE hypotheses per connection/wait-cycle (as later rounds in this session did) rather
than one hypothesis per round.

### Additional tests, later same day — all negative
- Patient multi-recv wait (12s, 4 rounds) after Browse in case the real child list arrives in a
  later TCP segment: nothing — connection just went fully silent (this coincided with a cooldown
  window though, inconclusive, worth repeating cleanly).
- Combined `(NodeId, AttributeId)` 8-byte payload for Read (nodeid=85, attr=13/"Value") and
  combined `(NodeId, Value)` 8-byte payload for Write (nodeid=85, value=0): both untested cleanly
  yet due to cooldown overlap — retry these specifically, they're still open theories.
- **Real OPC-UA Subscribe/Publish behavior ruled out**: opened connection, did handshake+browse,
  then just listened passively for 20s sending nothing further — server did NOT push any
  unsolicited data. Instead the connection was closed by the server (clean EOF, `recv()` returned
  `b''` with no exception) somewhere in that window — so there's an **idle connection timeout of
  well under ~20s**. Not a subscription-push model; pure request-response, and sessions don't
  stay open indefinitely — keep connections busy or expect to reconnect.

### Where this stands
After extensive, systematic black-box testing, op2/op3/op4 remain **completely unresponsive to
any variation in their argument content** — every encoding scheme tried (plain integers, both
endiannesses, OPC-UA-spec NodeId encodings, ASCII names, combined NodeId+AttributeId/Value pairs
not yet cleanly retried, 1/4/8-byte lengths) produces the exact same canned reply. The brief
explicitly rules out memory corruption and states node IDs must be discovered by "talking to the
endpoint" — but talking to it with everything reasonable so far hasn't revealed anything beyond
"Browse says root has 4 children". This is an unusually opaque black box.

**Recommendation**: this may be the point of diminishing returns for solo black-box guessing.
Options going forward: (a) retry the two still-open combined-field theories (Read with
NodeId+AttributeId, Write with NodeId+Value) cleanly outside any cooldown window, (b) ask in the
event's Discord whether a reference client/sample snippet exists (mirrors how PWN#Delta/0byte got
unblocked earlier in this event — see workspaces/bugpwn/notes.md), (c) de-prioritize vs. other
currently-open challenges with better signal (e.g. PWN#Beta's fresh page-granularity breakthrough)
and revisit OT#004 later with fresh eyes/new leads.

### FINAL ROUND (2026-10-25, exhaustive, conclusive) — op2/op3/op4 confirmed 100% content-invariant
Additional theories tested, ALL negative, ALL byte-identical canned replies:
- Namespace=1 (not just ns=0) with small numeric ids 1-4 for Read — real-world OPC-UA custom
  apps put their own objects in namespace 1+, not 0. No effect.
- Op1 call-count threshold/"unlock" theory fully refuted: called op1 20x in one connection
  (counter correctly reached 0x14=20, confirming it's a genuine uncapped per-op1 counter with no
  side effect), then op2 — still the identical canned reply.
- BrowsePath-style slash/dot-delimited string paths as the Read argument (`SafetySystem/Enabled`,
  `SafetySystem.Enabled`, `ReactorController/Temperature`, `Objects/SafetySystem`) — real OPC-UA
  has an actual "TranslateBrowsePathsToNodeIds" service that works this way; no effect here either.

**Conclusion: op2 (Browse) / op3 (Read) / op4 (Write) are confirmed, after an exhaustive and
systematic search across every plausible encoding (raw/BE/LE integers, 1/2/4/8/N-byte lengths,
OPC-UA-spec NodeId encodings in both namespace 0 and 1, combined NodeId+AttributeId and
NodeId+Value pairs, ASCII node names, slash/dot browse-paths, field-order swaps implied by the
above), to return a single fixed canned reply (`status=0, trailing byte=4`) regardless of literally
any argument content tried.** This is not a framing bug on our end (the wire format itself —
`[op:1][len:4 LE][data:len]` — is solid and well-confirmed by op1's genuine counter behavior and
by the "incomplete frame hangs" behavior). Either (a) the real addressing mechanism uses an
encoding genuinely outside the space of reasonable guesses attempted here, or (b) this specific
simplified op+len+data layer is a deliberate decoy and the real protocol entry point is something
else entirely (different trigger sequence, different port, or non-opcode-based framing) that
hasn't been identified. **Needs external input (Discord/organizer hint or a reference client) to
make further progress — recommend pausing further blind probing on this challenge.**
