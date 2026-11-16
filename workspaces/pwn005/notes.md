# PWN#005 (id 27, pwn, 150->40 decay, max_attempts=3)

- Description: "Get a shell on the remote host and read the flag."
- Connection: 169.58.126.107 5008
- No files attached.
- Dropped by admin announcement ~14:54 UTC, visible in API ~45min later (19:38 UTC check).

## Blackbox recon (no binary provided, files=[])
Menu: `1) Peek memory` (prompts Address, Length), `2) Checkout` (prompts a free-text note),
plus an **undocumented hidden option `9`** (not listed in the menu text).

### Peek memory
- Length cap: valid 1-1024, >1024 -> "Invalid length." (boundary confirmed: 1024 ok, 2048+ rejected).
- Returns ZERO bytes (confirmed via raw hexdump, not a display/strip artifact) for every address
  guessed so far: non-PIE text range 0x400000-0x410000 (1 page step), typical PIE base range
  0x555555554000-0x55555555a000, typical libc/ld mmap range 0x7ffff7c00000/0x7ffff7fcf000.
  -> Consistent with PIE+ASLR active and no leak yet to anchor a real address (blind guessing a
  ~28-bit-entropy PIE base is infeasible, and irrelevant anyway since each TCP connection forks a
  fresh process with its own random base -- a hit in one connection doesn't transfer to another).

### Checkout (the overflow)
- Reads into a fixed stack buffer via a note prompt. Confirmed boundary via EOF/close detection
  (not just timeout): note length <=70 -> survives, returns to menu normally ("Thanks for
  visiting." + menu reprinted). Note length >=72 -> connection closes (process crash), no
  "*** stack smashing detected ***" message observed.
  => buf[64] + saved rbp (8 bytes) = **offset 72 bytes to control the return address** (classic
  x86-64 frame, looks canary-less based on absence of the glibc smash message, though a canary
  that simply isn't printed on crash can't be fully ruled out blackbox).
- No ret2win/ret2libc built yet: without a binary, no gadget addresses, no known `system`/`win`
  function location, and PIE means we can't aim RIP anywhere useful without a same-session leak.

### Hidden option "9" -- leaks "session: 0x<16hex> 0x<16hex>"
- Stable within one TCP connection (repeated `9` calls return identical pair); different pair on
  every new connection (so it's generated once at connection/process start, not per-call).
- Collected 14 samples total. Pattern found: the two values in a pair ALWAYS share their exact
  top 16 bits (verified via a^b having 0x0000 in the top 16 bits across all samples), while the
  remaining 48 bits look fully independent/random between the two values of a pair.
- Ruled out: NOT real x86-64 user-space pointers (canonical userspace addresses must have bits
  47-63 == 0; our top-16-bit field is nonzero and highly variable across sessions, e.g. 0xcb05,
  0x962b, 0x51d4, 0xec60...). Ruled out time-seeding: no correlation found between wall-clock
  request time and the shared top-16-bit value across 6 time-stamped samples (jumps around
  non-monotonically) -- so it's not a low-res time(NULL)-seeded PRNG in any simple way tested.
- Current best guess: some kind of per-connection random token/state (two outputs sharing a
  common high-order "key"/"salt" component, independent low 48 bits) -- structure not yet
  understood well enough to predict or to derive a usable memory address from it.
- NOT yet tried: feeding these session values directly into "Peek memory" as the address (in the
  SAME connection) to see if they resolve to mapped memory despite failing the "canonical pointer"
  sanity check -- worth trying since the challenge may use a non-standard/scrambled addressing
  scheme on purpose.

### External recon
- WebSearch for a public GitHub repo with this challenge's binary (same pattern that resolved
  PWN#Delta/0byte in prior editions) came up empty -- no indexed repo for "bugpwn battleCTF 2026"
  pwn binaries, no "Document Store" challenge writeup found.
- NOT yet tried: asking in the CTF Discord (#général) the way the 0byte lead was found previously
  -- past precedent (0byte, PWN#Delta) shows other players/organizer sometimes surface binaries or
  hints there. This needs the user (their own Discord account/judgment), not something to automate.

### UPDATE: option 9 structure cracked (partially) -- a^b is a real canonical address
Collected 8+ samples of (a,b) pairs. `a ^ b` consistently lands in the canonical 47-bit userspace
range (< 0x800000000000) and clusters tightly across samples (~0x29e2_xxxx_xxxx to
~0x2a9d_xxxx_xxxx, i.e. differs only in the low ~40 bits, consistent with normal ASLR entropy for
a single mapped region). This strongly suggests: `a` = a raw random secret (likely the canary),
and `b = a XOR real_address` (XOR-obfuscated leak -- a real pointer's top 17 bits are all 0, so
XORing with it doesn't change a's top-16-bit field, which is exactly what we observed/initially
mistook for "shared high bits"). **a^b is very likely a genuine stack-address leak.**
- HOWEVER: feeding `a^b` (and a^b +/- 8/16, and raw a, raw b) into "Peek memory" in the SAME
  connection still returned zero bytes every time (tested live, 2026-10-18 ~20:20 UTC).
- Working theory on why: a^b is probably the address of a stack-local variable *inside the
  function that handles option 9 / the leak*, not necessarily inside the still-valid stack frame
  of the *menu loop* "Peek memory" reads from -- by the time we send the follow-up "1" command,
  that frame may already be gone/overwritten (stack is reused per call), so the leaked address may
  no longer hold readable/mapped-the-same-way data, OR "Peek memory" itself may be non-functional/
  a deliberate red herring independent of address correctness (every single address scheme tried
  -- non-PIE text, PIE text, libc/ld bases, small indices 0-10, negative indices, a, b, a^b and
  neighbors -- returns byte-for-byte identical empty output, which is also consistent with the
  read primitive being broken/always-empty regardless of input).
- NOT yet tried: using a^b (or an offset from it) as the **overflow return-address target** in
  Checkout directly, rather than as a Peek address -- i.e. skip trying to read memory and instead
  just blindly ROP/ret using the leaked value as-is as the hijacked RIP (e.g. if it's a stack
  address, maybe it points at attacker-controlled bytes already on the stack -- a stack-pivot-ish
  idea) or as a stack-leak to compute canary/saved-rbp context for a cleaner ret2libc once we also
  get a libc leak. This needs the actual binary to be more than a guess, though.

### Status: BLOCKED. Blind peek-address guessing is now exhausted (every tried scheme: raw
non-PIE/PIE/libc bases, small/negative indices, and the a^b leak + neighbors, all return
byte-identical empty responses -- "Peek memory" may simply be non-functional/decoy).
The one solid lead is the a^b XOR-leak (very likely a real stack pointer) from hidden option "9",
but turning it into RCE needs either the actual binary (to know what's at/near that address and to
build real ROP) or a lot more blind trial on the Checkout overflow target itself. Recommend getting
the binary (Discord/organizer -- same path that unblocked PWN#Delta/0byte in past editions) before
sinking more time into further blackbox guessing.

### Tried: blind ret2shellcode using the a^b leak as the hijacked return address (2026-10-18 ~20:25 UTC)
Payload: 27-byte x86-64 execve("/bin/sh") shellcode + NOP padding to 64 bytes + junk saved-rbp (8
bytes) + a^b (leaked same-connection) as the 8-byte return address. Sent via Checkout in the same
connection right after leaking via option 9. Result: normal crash (connection closed after "Thanks
for visiting."), no shell, no distinguishable different behavior. Expected outcome given NX is
virtually always enabled by default on modern toolchains/kernels -- this was a cheap one-shot test,
not a strong signal either way about whether a^b is exactly on-target.

### Conclusion: genuinely needs the actual binary now
All reasonable-cost blackbox techniques are exhausted: arbitrary-address read never returns data
for any input tried; the only working non-menu primitive (hidden option 9) resolves to a real
leaked address via XOR but we have no way to know what's near it or build real ROP without the
binary; blind ret2shellcode on that address failed as expected under NX. Further progress requires
either the actual ELF (ask in Discord/organizer, as worked for PWN#Delta/0byte previously) or the
user explicitly wants more blind attempts despite low expected value.

## STATUS CHECK (2026-10-25 15:11 UTC)
- Platform metadata (id=27): value=124, solves=14, solved_by_me=False, attempts=0, state=visible.
  connection_info `169.58.126.107 5008` unchanged. `files=[]` still — no binary has been attached
  by organizers since last check, so the "need the actual ELF" blocker is still unresolved
  platform-side.
- Most promising next concrete step: ask in Discord/organizer channel for the missing binary
  (same path that previously unblocked PWN#Delta/0byte), since all blind blackbox techniques are
  exhausted and no new attachment has appeared.

## STATUS CHECK (2026-10-25, re-verified)
- Re-fetched `show-challenge --id 27`: value=124, solves=14, solved_by_me=false, attempts=0,
  state=visible, max_attempts=3, connection_info `169.58.126.107 5008` unchanged.
  **`files=[]` — still no attachment.** No mid-event patch has happened for this challenge (unlike
  PWN#006's description-only update). The "need the real ELF" blocker remains unresolved
  platform-side as of this check.
- Per instructions, did NOT re-run any of the already-exhausted blind/blackbox techniques (peek
  address sweep, hidden option 9 XOR-leak analysis, blind ret2shellcode). Only action taken: one
  light reachability probe (raw TCP connect + read banner, no further interaction) to confirm the
  service is still up and unchanged:
  ```
  recv() -> b'=== Document Store ===\n1) Peek memory  2) Checkout\n> '
  ```
  Banner text and menu are byte-identical to what's documented above — service is alive, nothing
  about it appears to have changed.
- Conclusion: still blocked exactly as before. Nothing new to act on without the binary. Next step
  is still organizer/Discord outreach for the attachment, or an explicit decision from the user to
  keep sinking time into blind blackbox attempts despite the already-documented low expected value.

### Agent run 2026-10-28 -- calibration test + new findings (still BLOCKED)

Ran the prescribed single-connection calibration procedure (never attempted before): leak via
option 9, then a SAFE Checkout note (`b"CAFEBABE"*8`, 64 bytes, no crash), then sweep "Peek memory"
around `a^b` in the SAME connection/process, searching returned bytes for the marker.
**Result: zero bytes returned for every address tried, exactly like all prior attempts.**
Windows swept around `a^b` this run: +/-0x2000 (step 896), then widened once to +/-0x3000 (step
896, overlapping reads to avoid missing a split marker) -- all 0-byte responses, marker never found.

**New finding 1 -- a second undocumented hidden menu option, "7"** (previously only "9" was known).
A quick scan of `0,3,4,5,6,8,10,-1,99,""` found option `7` also returns a `session: 0x.. 0x..` pair
(same format as option 9), while all the others return `Invalid.`. Characterized it:
- Option 7's pair is **stable across repeated calls within a connection**, like option 9's.
- Option 9's pair is **unchanged by an intervening safe Checkout call** (new confirmation -- not
  explicitly tested before): called 9, then did a safe 64-byte Checkout, then called 9 again in
  the same connection -- identical values both times.
- Relationship between the two options' first values: `a7 - a9 == 7` consistently (tiny, constant
  offset), and `a9 ^ a7` is a correspondingly tiny value (0xb in one sample). This is consistent
  with both `a9` and `a7` being `(same per-connection secret) XOR (address of some small, nearby
  stack-local variable)`, where the two local variables (one per option's handler) sit only ~7-11
  bytes apart on the stack.
- However, `a7 ^ b7` itself is a SMALL value (e.g. 0x34fe), not canonical-leak-sized -- this does
  NOT fit the "a=secret, b=secret^address" model that fits option 9's pair. It's more consistent
  with `a7` and `b7` both being raw obfuscated values whose underlying real addresses are close
  together (so their XOR is small), i.e. option 7 may leak a *pair of nearby stack slots* rather
  than a single far-away address like option 9 appears to.
- Computed every plausible cross-combination (`a9^b9`, `a7^b7`, `a9^a7`, `b9^b7`, `a9^b7`,
  `b9^a7`) across a fresh connection and swept "Peek memory" (safe-Checkout-marker method) around
  every "large" (canonical, non-trivial) candidate: `a9^b9`, `b9^a7`, `b9^b7`. **All zero bytes,
  no marker found, in every window.**

**New finding 2 -- Peek's "Address" field shows NO format sensitivity at all**, which had not been
tested before (previous attempts only ever sent `0x`-prefixed hex). Tested side-by-side in one
connection: hex (`0x400000`), plain decimal (`4195376`), hex digits with no `0x` prefix (parsed as
decimal `400000`), non-numeric garbage (`"notanumber"`), negative (`"-1"`), and explicit `"0"`.
**Every single one produced the byte-identical response** (`Address: ` / `Length: ` prompts, then
just `\n` + menu reprint, i.e. 0 bytes, no distinguishing error for the garbage/non-numeric input
either). This is a materially stronger signal than before: a real `scanf`/`strtoul`-based parser
would normally behave differently for valid-vs-garbage input (different leftover-buffer/sync
behavior at minimum), yet behavior is 100% uniform regardless of input validity. Combined with
finding 1's negative sweep results, this pushes the assessment from "maybe we haven't calibrated
the right address yet" to **"Peek memory most likely never returns data for any input -- it looks
functionally dead/decoy in this blackbox testing,"** independent of which address/leak is used.

**New finding 3 -- sharper (though still not 100%-binary-confirmed) argument that there is NO
stack canary**, derived from data already in this file (no new network round-trip needed, just a
cleaner deduction than previously written): if a canary occupied bytes 65-72 of the frame (the
classic `buf[64] + canary[8] + saved_rbp[8] + ret[8]` layout), then a 70-byte note (which already
overwrites bytes 65-70, i.e. 6 of the canary's 8 bytes) would corrupt the canary and should trigger
glibc's `__stack_chk_fail` abort on return -- but the existing data shows a 70-byte note returns to
the menu completely normally with no crash and no "*** stack smashing detected ***" message. A
corrupted canary cannot silently survive a function return in glibc's default build. Therefore the
layout is most likely truly `buf[64] + saved_rbp[8]` with **no canary**, matching the already-
confirmed offset-72-to-return-address finding, now on firmer logical footing (still blackbox, no
binary to grep for `__stack_chk_fail` calls, but the behavioral argument is now tight).

**Hidden-option sweep result (secondary lead from the task, now done):** `0,3,4,5,6,8,10,-1,99,""`
all return `Invalid.`; only `7` (new) and `9` (known) are live. No further undocumented options
found.

### Status: still BLOCKED, with a materially expanded and more conclusive evidence base.
Summary of what's new vs. prior sessions (nothing below was previously tried):
1. The exact prescribed calibration test (safe-note marker + same-connection Peek sweep around
   `a^b`) -- done, failed (0 bytes, no marker, in two window sizes).
2. Discovered and characterized a second hidden option (`7`), computed and swept every cross-XOR
   combination between its leak and option 9's leak -- all candidates still return 0 bytes via
   Peek.
3. Proved Peek's input parsing is format-insensitive (hex/decimal/garbage/negative/zero all
   produce an identical response) -- strong new evidence Peek is non-functional/decoy regardless
   of address, not just "wrong address guessed."
4. Confirmed option 9's leak is unchanged by an intervening safe Checkout (stack reuse doesn't
   perturb the leaked values within a connection).
5. Tightened the no-canary argument using already-collected boundary data (70-byte note survives
   intact -> a canary in bytes 65-72 cannot have survived that).
Net effect: the overflow (offset 72, no canary, PIE) is still the only confirmed-working exploit
primitive, and there is still no way in this blackbox session to turn either hidden-option leak
into a usable memory read or a crash-free address for a ret2shellcode/ROP target. Peek memory now
looks very likely to be dead weight / an intentional red herring rather than an uncalibrated
primitive. Further progress still realistically requires the actual binary (Discord/organizer
outreach, as in past editions) -- blind guessing has now been pushed substantially further than
before without success, so continuing to guess has very low remaining expected value. No flag
obtained; nothing written to `flags/pending/`.

### Agent run 2026-10-28 (continued, user-authorized) -- overflow-as-oracle experiment: also BLOCKED

New idea (never tried before, suggested by the user/coordinator since Peek looks dead): instead of
using "Peek memory" to confirm a target address, use the Checkout **overflow itself** as a timing/
closure-type oracle. One connection per candidate return address; send `b"A"*64 + b"B"*8 +
pack("<Q", candidate_addr)` as the note (triggers the known offset-72 overwrite), then measure (1)
how the connection closes (`EOF`/orderly-FIN vs `RESET`/RST vs `TIMEOUT`/still open), (2) elapsed
time from send to closure, (3) any bytes received before closure. Idea: a mapped-but-wrong-type
page (e.g. non-executable NX mapping) vs a truly unmapped address vs a non-canonical address might
produce different fault types/timings even without Peek working.

Ran 27 connections total (within the "stay reasonable, 10-15 per family" budget):
- 1 baseline: a known-safe 70-byte note (no overwrite) -> `closure=TIMEOUT` (connection stays open,
  socket still alive after 1.1s), data = `"Thanks for visiting.\n" + menu` -- confirms the detection
  method correctly tells "survived" apart from "crashed".
- 1 baseline: obviously-garbage/non-canonical return address `0x4141414141414141` -> `closure=EOF`,
  elapsed **0.0977s**, data = `"Thanks for visiting.\n"` only (then immediate close).
- 9x non-PIE family `0x400000` to `0x408000` step `0x1000`.
- 7x PIE-typical family `0x555555554000` to `0x55555555a000` step `0x1000`.
- 9x leak-based family: fresh connection each time, leak `a9^b9` via option 9, target =
  `(a9^b9) + offset` for `offset in {0, +-8, +-16, +-0x100, +-0x1000}`.

**Result: all 25 non-baseline candidates (and the garbage baseline) produced byte-identical
behavior**: `closure=EOF`, elapsed **0.097-0.102s** (no measurable timing variance outside normal
network jitter), data = exactly `"Thanks for visiting.\n"` then immediate close, every single time
-- indistinguishable from the deliberately-garbage/non-canonical baseline. No address family
(non-PIE guess, PIE guess, or any leak-derived candidate incl. small offsets) produced a different
fault signature, a delayed close, extra output, or a still-alive connection. The oracle shows
exactly one of two states (`TIMEOUT`=survived vs `EOF`=crashed) and every single tested address
--valid-looking or garbage-- falls into the "crashed, ~0.1s, no extra output" bucket.

**Conclusion: this oracle gives zero differentiation between address validity.** Two plausible
reasons, can't distinguish between them blackbox: (a) all 25 real guesses are simply wrong/
unmapped (as or more likely than not, since they're blind guesses against an unknown binary/ASLR
state, no different from the baseline garbage address), or (b) the crash-to-close path is uniform
at the OS level regardless of fault type (SIGSEGV from an unmapped page vs a non-canonical #GP vs
a NX violation all result in the same "process dies, kernel closes the socket via orderly
shutdown" sequence from the TCP peer's point of view, at the same ~100ms scale) -- i.e. this
particular side channel (socket-level timing/closure type) may be fundamentally too coarse to ever
distinguish fault types for this service, independent of which addresses are tried.

**Status: still BLOCKED.** This was a genuinely new technique, cleanly executed and validated
(the safe-vs-crash baseline contrast confirms the methodology itself works), and it returned a
clean negative result rather than an inconclusive one. Combined with the exhausted Peek-calibration
and hidden-option work from earlier in this run, essentially every low-to-medium-cost blackbox
avenue identified so far (leak-address calibration, format-sensitivity probing, hidden-option
discovery, cross-leak combinations, and now overflow-as-timing-oracle) has been tried and has
failed to produce a working read/write/info primitive beyond "the overflow itself crashes the
process at offset 72, no canary, PIE active." No flag obtained; nothing written to
`flags/pending/`. Recommend not sinking further blind-guessing time into this channel; the
remaining realistic path is still obtaining the actual ELF (Discord/organizer outreach).

### Agent run 2026-10-28 (continued) -- partial-overwrite (1-byte low-byte of retaddr) test: INCOMPLETE, no signal in partial data

New technique requested (standard PIE/ASLR-bypass idea, never tried before): overwrite only the
LOW byte of the return address (note length 73 = offset-72 confirmed + 1 controlled byte, leaving
the other 7 high bytes of the original/legitimate return address on the stack untouched), then
brute-force all 256 values for that byte, one fresh connection per value, looking for any value
that survives (TIMEOUT instead of EOF) or otherwise behaves differently.

Ran this brute force; **it was interrupted mid-run by a transient network blip** ("OSError: [Errno
113] No route to host" partway through, after ~128-160/256 values in the first attempt -- almost
certainly rate-limiting/connection-flood protection on the target infra reacting to the very high
volume of fresh TCP connections made across this whole session's testing, similar in spirit to the
already-known "HTB Pro Lab full-port-scan cooldown" pattern in memory, though this is a different
platform). Connectivity recovered on its own within seconds (confirmed with a plain connect test).
Restarted with a more resilient version (retry-with-backoff per connection, incremental JSONL
writes, small delay between connections) -- **this run did not finish before the session ended.**

**Partial result collected so far: byte values 0x00 through 0x18 (25/256), ALL closure=EOF, ALL
identical data `"Thanks for visiting.\n"`.** No survival, no distinguishable behavior in this
partial sample. This is consistent with (but does not yet prove) the same pattern seen everywhere
else in this file -- but the sweep is far from complete and must not be treated as a refutation.

**Not yet tested: byte values 0x19-0xFF (231/256 remaining).** The 2-byte sampling pass (note
length 74, sampled every 0x10 or 0x100) was not started at all.

**NEXT SESSION MUST:** re-run the 1-byte brute force to completion (resume from 0x19 if reusing
partial data, or just redo all 256 -- cheap, ~256 connections with small delays to avoid tripping
the same rate-limit again, e.g. keep the 0.08s inter-connection delay or increase it slightly).
If a connection error like "No route to host" recurs, back off for ~30-60s before retrying rather
than hammering through it (the earlier HTB memory note suggests cooldowns on aggressive connection
volume can last 20-30+ min in the worst case on some infra -- watch for that pattern specifically
if retries keep failing, and treat it as time-based, not an exploit signal). Only after the full
256-value sweep is done (and confirmed with repeats if something looks interesting) should the
2-byte sampling pass begin. This whole technique is still OPEN, not refuted and not confirmed.

**UPDATE (same run, consolidated retry):** per coordinator instruction, replaced the earlier
piecemeal approach with ONE self-contained script, `/tmp/pwn005_sweep.py`, launched fully detached
via `nohup ... &; disown` (so it survives this agent session ending) and writing to:
- `/tmp/pwn005_sweep_1byte.jsonl` -- raw per-byte results for the 256-value 1-byte sweep.
- `/tmp/pwn005_sweep_2byte.jsonl` -- raw results for the 2-byte sampled sweep (step 0x100 across
  0x0000-0xFFFF), only run automatically if stage 1 finds nothing reproducible.
- `/tmp/pwn005_sweep_summary.txt` -- the script's own final plain-text verdict, written once at
  the very end of its run (it automatically re-tests any "interesting" value 3x before counting it
  as a confirmed signal, to filter out the kind of one-off network jitter seen earlier in this
  file).
- `/tmp/pwn005_sweep.log` -- full stderr/progress log (`progress: N/256` lines, `DONE` on exit).
This was still running (stage 1, ~15/256) when this update was written. **Next session (or later
in this one): read `/tmp/pwn005_sweep_summary.txt` first for the verdict; if that file does not
exist yet, the sweep is still running or was killed -- check `/tmp/pwn005_sweep.log` for the last
progress line and `ps aux | grep pwn005_sweep` for whether the process is still alive before
re-launching anything (avoid running two sweeps against the target at once).**

### Agent run 2026-10-28 (continued) -- checked an external/unverified claim: REFUTED

The coordinator relayed an unverified, possibly-hallucinated claim from another tool/agent log,
asked to be checked rigorously and skeptically rather than trusted. Claim had three parts:
(1) the real return-address offset is 80, not 72 (theory: an uncounted trailing NUL from
gets/scanf/strcpy shifted the original calculation); (2) a sweep with the "corrected" offset
would find addresses in `0x401300-0x401c70` producing behavior distinguishably different from
immediate-crash/garbage; (3) if true, that would mean the binary is non-PIE with fixed addresses.

**Step A -- fine-grained offset re-measurement.** Tested note lengths 68-82 individually (not just
a binary threshold), 3 fresh connections per length, recording exact closure type:
- Lengths 68, 69, 70, 71 -> `TIMEOUT` (connection survives, process returns to menu normally), 3/3
  reps each, zero flakiness.
- Lengths 72 through 82 -> `EOF` (process crashes, connection closes), 3/3 reps each, zero
  flakiness.
**Result: the crash boundary is a clean, perfectly reproducible step exactly between length 71 and
72.** No evidence whatsoever of an 80-byte boundary, no partial/intermediate behavior anywhere in
68-82. **Claim (1) is REFUTED** -- the previously-documented offset of 72 is correct and now
confirmed with per-length granularity + repetition, not just the original single-threshold check.

**Step B/C -- re-ran the overflow-oracle test using the (confirmed-correct, unchanged) offset-72
payload layout** (`"A"*64 + "B"*8 + pack("<Q", addr)`, 80 bytes total note length) against:
- 2x garbage baseline (`0x4141414141414141`), 2 reps.
- A dense sweep of the specific claimed-interesting range `0x401300-0x401c70`, step `0x40` (37
  addresses), **2 reps each** to rule out flakiness before concluding anything = 78 total
  connections.
**Result: all 78 tests, including the garbage baseline, produced `closure=EOF` and identical data
`"Thanks for visiting.\n"`, i.e. byte-for-byte indistinguishable from each other and from the
garbage baseline.** One single data point (`0x401640`, rep 1) showed `elapsed=3.68s` vs. the usual
~0.10s, but the SAME address's rep 0 was a normal ~0.10s, and closure/data were identical in both
reps -- this is ordinary network jitter, not a reproducible signal, and does not survive the
"repeat before concluding" check the coordinator asked for. **Claim (2) is REFUTED** -- no address
in the specified range (or the garbage baseline) shows any distinguishable behavior with the real,
confirmed offset.

**Claim (3) (non-PIE) is therefore unsupported** -- it was entirely conditional on (1)/(2) being
true, and both were cleanly refuted by direct, repeated testing against the live target.

**Conclusion: the external claim was false/hallucinated.** This session did its job correctly by
treating it as a hypothesis and testing it rather than trusting it -- the real offset remains 72
(now confirmed with much finer granularity + repetition than before), and the specific "interesting
non-PIE range" shows zero behavioral difference from garbage, consistent with all prior
blackbox findings in this file. No new ground gained; status remains BLOCKED exactly as in the
immediately preceding section. No flag obtained; nothing written to `flags/pending/`.

### Coordinator run 2026-10-28 (final) -- partial-overwrite sweep completed + manually verified: still BLOCKED

The detached `/tmp/pwn005_sweep.py` (launched by the agent, survived its session via `nohup`+
`disown`) finished its full run (710.5s total) while the agent itself was no longer active;
the coordinating session (not the subagent) read the results directly and did additional manual
verification.

**Stage 1 (1-byte sweep, all 256 values, note length 73) -- script's own result:** flagged 3 raw
candidates as momentarily "interesting" (`0x8c`, `0xc9`, `0xcf`, each a `TIMEOUT` instead of the
usual `EOF`), but its own built-in 3x-repeat verification immediately refuted all three
(`all_interesting=False` -- on repeat, all three show the completely standard crash signature:
`closure=EOF`, data=`"Thanks for visiting.\n"`, ~0.1s). **The coordinator independently
re-verified this by hand (4 fresh connections per byte value, plus a live follow-up command sent
after each) and got the identical result: 0x8c/0xc9/0xcf are false positives, indistinguishable
from any other crash.**

**Important finding the script's own heuristic missed entirely: byte value `0x00`.** Manual
testing (4/4 repeats) shows `0x00` reproducibly: `closure=TIMEOUT`, full data
`"Thanks for visiting.\n1) Peek memory  2) Checkout\n> "`, and -- critically -- sending a further
command (`"1\n"`) after that gets back `"Address: "`, proving the process is genuinely alive and
back in its normal interactive menu loop, not just slow to close. **This is a real, reproducible,
non-crash result**, never seen for any other byte value in this entire investigation. Likely
explanation: `0x00` is simply the TRUE original low byte of the legitimate return address --
overwriting with the value that was already there is a no-op, so of course it survives. This
*validates the partial-overwrite mechanism works as designed* (the other 7 untouched high bytes
of the real return address are preserved and the process returns correctly when the 1 touched
byte happens to be correct) and gives us one real fact (`real_retaddr & 0xFF == 0x00`, plausible
for a 16/256-byte-aligned function entry), but it is **not by itself a new code-execution
primitive** -- it only confirms we can restore the status quo, not reach anywhere new.

**Stage 2 (2-byte sampled sweep, note length 74, byte0 fixed effectively at the pattern
`(k*0x100) & 0xFF == 0`, byte1 = k for k in 0..255) -- result: zero candidates flagged at all,
not even a repeat of the byte0=0x00-alone success.** This deserves a methodological caveat before
treating it as a clean refutation: **this stage used only ONE connection per candidate value, no
repeats.** Per Linux PIE ASLR (page-granularity, ~bit 12 and up randomized per forked process),
the low byte (bits 0-7) is fully deterministic/compile-time-fixed (consistent with the stage-1
result), but byte 1 (bits 8-15) straddles the boundary: bits 8-11 are deterministic, bits 12-15
are randomized fresh on every new TCP connection (new forked process = new random base). A
single-shot test of a fixed byte-1 candidate against a fresh (randomly-based) connection only has
roughly a 1-in-16 chance of matching even when its deterministic nibble (bits 8-11) is correct,
because the random nibble (bits 12-15) also has to coincidentally match by luck. With no repeats,
getting zero hits across 256 single-shot trials is not strong evidence of absence (expected hits
under the correct-low-nibble hypothesis is only ~1, and getting 0 by chance alone has roughly a
35% probability) -- so **stage 2's "no signal" is statistically weak, not a clean negative like
stage 1's or the earlier overflow-oracle experiment.**

**Final assessment and recommendation (coordinator, not a repeat of the subagent's own
over-strong "EXHAUSTED" framing):**
- The partial-overwrite technique **does work** as a mechanism (proven by the reproducible `0x00`
  result) and did yield one real fact about the binary's layout (`real_retaddr & 0xFF == 0`).
- It did **not** yield a new, reachable code location, a read primitive, or anything resembling a
  shell/flag.
- Pushing this further toward a full BROP-style (Blind ROP) blind exploitation chain -- the
  textbook technique for exactly this scenario (forking server, stack overflow, no leak, no
  binary) -- is *possible in principle* but would require: (a) redoing byte-1 properly with many
  repeats per candidate to reliably extract its deterministic nibble (a few hundred more
  connections, still cheap), then (b) searching for a genuine "stop gadget" (a DIFFERENT valid,
  non-crashing code address, not just the original return restored) via much more extensive
  blind probing, then (c) chaining that into a call to a leak-capable function (e.g. `write`) to
  dump the real binary over the socket -- a multi-hour-to-multi-day specialized effort even for an
  experienced blind-ROP practitioner, with no guarantee of success and only 3 flag-submission
  attempts total on this challenge (irrelevant to recon cost, but a reminder of how little margin
  there is if something is eventually found).
- Given the time already invested across this whole run (Peek-memory calibration, hidden option 7,
  format-insensitivity, cross-leak XOR combinations, overflow-as-timing-oracle, offset
  fine-measurement, the refuted external claim, and now the partial-overwrite sweep), **the
  realistic, proportionate call is: still blocked for practical purposes.** The only clearly
  worthwhile easy follow-up left (if anyone wants to spend ~10-15 more minutes of cheap recon
  before giving up entirely) is a *properly repeated* byte-1 sweep (each of the 256 candidates
  tried ~16-32 times instead of once) to settle whether the deterministic nibble is recoverable --
  but even a full success there only yields ~12 bits of the address, nowhere near enough to defeat
  ASLR's remaining entropy without a genuine stop-gadget/leak chain. **Getting the real ELF via
  Discord/organizer remains overwhelmingly the better use of remaining time.**

No flag obtained at any point in this entire investigation. Nothing written to `flags/pending/`.
No platform submission attempted (0/3 attempts still unused).
