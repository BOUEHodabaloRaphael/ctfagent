# PWN#001 (pwn, 100 pts) — in progress, unusual blocker found

Target: 169.58.126.107:5000. Binary `vault` (not stripped, No PIE, Full RELRO, canary, NX),
`libc.so.6` + `ld-linux-x86-64.so.2` given (matching libc for ret2libc).

## Binary structure (confirmed via objdump, 100% verified against live behavior)
- `vuln()` (0x401220): buffer at `rbp-0x50` (80 bytes). Two reads into the SAME buffer:
  1. `read(0, buf, 0x49)` (73 bytes) → then `puts(buf)` ("Hello, " + buf).
  2. `read(0, buf, 0x100)` (256 bytes, the real overflow) → `puts("Message received.")` →
     canary check → `leave; ret`.
- Canary at `buf+72` (i.e. `rbp-0x8`). Saved RBP at `buf+80`. Return address at `buf+88`.
  **These offsets are 100% empirically confirmed** (see bisection results below).
- `gadgets()` (0x4011ee) is a hand-placed ROP helper; the useful instructions start at
  **0x401205**: `pop rax; xchg rdi,rax; ret` (functions as `pop rdi; ret`). A clean bare
  `ret` is also available at **0x401208** (tail of the same function, useful as an
  alignment-filler gadget).
- `puts@plt`=0x401030, `puts@got`=0x403fc8, `main`=0x4012d1, `vuln`=0x401220.

## Canary-leak technique (CONFIRMED WORKING, reliable)
Send exactly 73 bytes (all non-null, e.g. `b'A'*73`) as the "name". This clobbers the
canary's leading byte (always `0x00` by glibc convention) with our own non-null byte,
so the subsequent `puts(buf)` over-reads past our input into the canary's remaining 7
bytes (and sometimes a bit of saved-RBP) until it hits the next null byte. Reconstruct:
`canary = b'\x00' + leaked[:7]`.
CAVEAT (found the hard way): if the real canary happens to contain a null byte within
its own first 7 bytes (~a few % of the time, random per connection), `leaked` comes back
shorter than 7 bytes and this naive reconstruction is WRONG (produces a short, misaligned
canary). Guard with `if len(leaked) < 7: reconnect/retry`.

## Offset bisection (fully confirmed empirically, remote target, no trailing-newline bug)
Payload = `b'A'*72 + canary + filler`, sent with **no trailing newline** (a real bug was
found and fixed: `io.send(payload + b'\n')` silently added one extra byte beyond the
intended length, corrupting whatever sat at that position — always use bare `io.send(payload)`
with exact-length payloads for this binary, it only consumes what's sent, doesn't need `\n`).
- filler len 0 (80 bytes total, canary only) → SURVIVES, loops back to "Enter your name".
- filler len 8 of 'B' (88 bytes, fills saved-RBP fully, return addr untouched) → SURVIVES.
- filler len 9+ (touches return address, even by 1 byte) → CRASHES (connection closes after
  "Message received.\n", no further output), REGARDLESS of whether the return-address bytes
  written are garbage OR a valid code pointer (tried `vuln` 0x401220 and `main` 0x4012d1
  explicitly — both still crash, exactly like garbage `'D'*8` does).

## The real blocker: ANY return-address overwrite kills the connection, even to valid code
This is the crux of the problem. Tried and ALL failed identically (silent close right after
"Message received.\n", no crash message, no extra output):
- Direct return to `vuln` (0x401220), 0 alignment-fixing gadgets.
- Direct return to `main` (0x4012d1), 0 alignment-fixing gadgets.
- Return via one `ret`-only gadget (0x401208) first, then `vuln`/`main` (to fix the
  16-byte stack alignment that a single simulated "call" via `ret`-landing is off by —
  confirmed by hand with the SysV ABI rule: callee entry needs `RSP % 16 == 8`; a bare
  `ret`-into-function lands at `RSP % 16 == 0` with these exact offsets, off by 8; adding
  one more bare-`ret` hop should fix it — it did NOT change the outcome).
- Full `pop_rdi → puts@got → ret-align → puts@plt → main` ret2plt leak chain — same silent
  close, no leak ever printed (not even partial output before the close).
- Ruled out: rate limiting / self-inflicted throttling from rapid reconnects (added an
  explicit `sleep(1)` before sending the overflow payload and a `sleep(15)` before a later
  attempt — identical outcome every time, fully deterministic, not time-dependent).
- Ruled out: TCP fragmentation / short reads (payloads here are 96–104 bytes, far under any
  MTU; and the deterministic bisection behavior — works ≤88, fails ≥89, every single time —
  is inconsistent with a flaky partial-read theory).

Net effect: **touching the return-address field at all, with anything, kills the process**,
while an identically-sized overflow that stops 1 byte short (saved-RBP fully overwritten,
return address untouched) is completely fine. This smells like either:
(a) an external monitor (ptrace/seccomp-based control-flow integrity watchdog) specifically
    guarding this stack slot / detecting a ROP-style corrupted-then-valid return address, or
(b) a misunderstanding on our part of where the TRUE return-address slot is that we haven't
    found yet despite the clean bisection (e.g. maybe there's a guard page or an additional
    hidden check compiled in that isn't visible in this static disassembly — e.g. CET shadow
    stack enforcement on the remote host, which WOULD explain exactly this symptom: the
    hardware shadow stack silently traps/kills the process the instant a corrupted-and-
    rewritten return address is used via `ret`, regardless of whether the new value is valid
    code, because shadow-stack CET compares the popped return address against its own
    protected copy and faults on ANY mismatch from the original — this is a growing default
    on newer Intel CPUs / distros and would perfectly explain silent, deterministic,
    content-independent kills exactly at the return-address boundary).

## Next steps (not yet tried)
- If CET/shadow-stack is suspected: this specific host/kernel config may simply not be
  exploitable via classical ROP/ret2libc at all — would need a CET-aware technique (there
  isn't a simple one for a CTF binary without JOP-friendly gadgets, or the challenge may
  expect a completely different vulnerability class instead of the stack overflow+ROP we've
  been assuming).
- Worth testing: does OUR OWN forged "valid" address even need to be the FIRST return? Try
  letting the overflow leave the return address as a SECOND overflow's target from a stack
  pivot instead of a direct ret — unlikely to help if it's truly CET.
- Consider asking in Discord #ask-me whether `PWN#001` is confirmed solvable via classic
  ROP, given the exact same "silent close on any return-address write" symptom — this is a
  strong, specific, reproducible signal worth sharing/asking about before sinking more time.

Status: PAUSED. Canary leak + full offset map are solid, reusable findings. The actual
code-execution step is blocked by something beyond a normal buffer-overflow mistake on our
side (exhaustively ruled out trailing-newline bug, short-canary edge case, alignment, and
rate-limiting as explanations) — needs either a CET-aware approach or external confirmation
this is even the intended path.

## CET check (readelf -n vault)
Binary's .note.gnu.property only declares `x86-64-baseline` ISA, NO explicit SHSTK/IBT
property. This weakens the "binary opted into CET shadow stack" theory (opt-in is usually
required per-binary for the kernel to enforce it) — doesn't rule out a host-wide/global CET
enforcement policy or an external ptrace-based monitor, but it's not a clean confirmation
either. The actual cause of "any return-address write kills the process, even with a valid
code address" remains unconfirmed.

## Session 2 (2026-10-07) — "real hacker" retry round, several genuinely new findings

### Retraction carried over from prior session
The previously-reported "split-send bypass" (send 88 safe bytes, delay, then send the
retaddr bytes separately) is a CONFIRMED FALSE POSITIVE. Verified by sending an empty name
for round 2 and observing that fragments of the intended "return-address" bytes show up as
round 2's name echo — proving those bytes were never written to the protected offset at all;
they just sat unconsumed in the TCP receive buffer and were picked up by the NEXT, separate,
smaller `read()` call. Do not revisit this technique in its current form.

### New finding 1: the canary-leak over-read is bigger than previously used — it leaks a stack address for free
The `puts(buf)` over-read (sending 73 non-null bytes as name) doesn't stop after 7 bytes —
it continues reading live stack memory until it hits an actual `0x00` byte, which usually
isn't until partway into the saved-RBP field. Example real capture: leaked blob was **13
bytes**, not 7: `leaked[0:7]` = canary bytes 1-7 (as always used), `leaked[7:13]` = the
**first 6 bytes of the saved-RBP slot** (`buf+80..+85`), with byte `buf+86` being the null
that stopped the leak (saved-RBP's own high bytes are 0x00, as all canonical Linux user
addresses are — this is WHY it reliably stops there, not a coincidence).
This saved-RBP value is `main()`'s frame pointer at the moment it called `vuln()` — i.e. a
genuine **stack address leak**, obtainable on every single connection, entirely through the
existing "safe" 73-byte probe (no write past offset 80 involved, so it can never trigger
the guard). Concretely: `buf_address = RBP_main_leaked - 0x70` (derived from main's
disassembly: `call vuln` pushes 8 bytes, vuln's `push rbp` pushes another 8 →
`VULN_RBP = RBP_main - 0x20`; and `buf = VULN_RBP - 0x50` per the `lea -0x50(%rbp)` in
vuln() → `buf = RBP_main - 0x70`).
**Caveat discovered while trying to use this**: this does NOT enable a classic "stack pivot
via corrupted saved-RBP" — `leave; ret` does `rsp := rbp` (register value, fixed per-call,
unaffected by what we write into the saved-RBP *memory* slot), THEN `pop rbp` (reads our
written value into the register, but this only affects what RBP becomes for whatever runs
*next*, not the current `ret`'s target), THEN `ret` pops from `rsp = VULN_RBP+8 = buf+88`
— always the real, fixed, untouched return-address slot. So corrupting the saved-RBP value
has no effect on this `ret`'s destination; this idea doesn't give RIP control. Still, the
free stack leak is a real, reusable primitive — just not sufficient alone. No way was found
to chain it into a second read/write at an arbitrary address (no other primitive exists;
`puts("Message received.")` after the overflow read is a static string, no second over-read
leak is available there).

### New finding 2: local reproduction PROVES the block is remote-environment-specific, not intrinsic to the binary
Ran the exact same `vault` binary locally (`pwntools process()`, same libc) and replayed the
identical byte-for-byte payloads used against the remote target:
- Safe 88-byte payload → survives locally (expected).
- Overwrite return address with the **identical original value** (`0x401301`) → **SURVIVES
  locally**, loops back to "Enter your name" completely normally.
- Overwrite return address with garbage (`'C'*8`) → crashes locally (expected: real SIGSEGV
  on an invalid `ret` target, totally mundane).
This is the key new data point: locally, "write the correct value back" behaves exactly as
any unmodified binary should (no effect). Remote, the IDENTICAL byte-for-byte test still
kills the connection (re-confirmed this session, see finding 3). Since the machine code is
identical in both cases, the difference can only come from something **outside the binary**
in the remote deployment (a wrapper/supervisor process, not a compiled-in check, and not a
seccomp filter baked into the binary's own `setup()` either, since that would behave
identically local vs remote on the same kernel family).

### New finding 3: packet-capture (tshark) analysis of the crash
Captured the TCP stream live during both a garbage-retaddr attempt and an identical-original-
value attempt. In both cases: the server sends "Message received.\n" normally, and then,
**~5-200ms later, in the very next server→client frame, sends a graceful FIN** (not a RST).
No extra bytes, no error text, nothing else — consistent with the traced process exiting
(crashing or being killed) right after the `puts()` call and before/during the canary-check/
`leave;ret` epilogue, and the kernel performing a normal connection teardown (FIN) because
there's no unread/pending data in the socket buffers at the time of death. This is new
confirmation (previously we only saw this indirectly via client-side EOFError) but doesn't
by itself distinguish "real SIGSEGV from a bad address" from "external ptrace supervisor
kills the tracee" — **both produce an identical graceful FIN from the client's point of
view in this scenario**. Given finding 2 (identical-value write survives locally but not
remotely), the most coherent working theory is a **dynamically-armed hardware write
watchpoint** (ptrace DR0-3 debug registers) set fresh, per-connection, at the live runtime
address of `buf+88`, by an external supervisor that must compute that address at runtime
(e.g. by breaking at the `read()` syscall entry and reading `RSI`, which holds the
destination buffer pointer) before re-arming per child process — this would explain every
single property observed across both sessions: value-independence, exact single-byte
offset precision, raw-socket/nc-identical behavior, and now the local/remote split.

### New finding 4 (negative result): connection has its own unrelated ~100-150 round cap
Tried "aging" a connection with ~100-150 cheap, fully benign rounds (short name/message,
never touching the guarded offset) before attempting the overflow, hoping a stateful/
windowed traffic inspector might stop watching after enough "boring" traffic. Result: the
connection itself dies on its own (EOFError) somewhere in the 100-150 round range / after
roughly 30-45s of total connection lifetime, **regardless of payload content** — this looks
like an unrelated idle/duration/round-count cap on the service itself (not something we can
leverage), and it never got far enough past this cap to test whether the guard was still
armed afterward. Dead end; don't retry "aging" as an evasion strategy.

### New finding 5 (negative result): no race condition from concurrent connections
Fired 8 simultaneous connections, each independently leaking its own canary and attempting
the identical-original-retaddr overwrite at the same time, hoping a shared/global ptrace
supervisor resource might race and miss arming the watchpoint for one of them. All 8 died
identically right after "Message received." (one looked like a survivor at first glance —
`d1`/`d2` split — but that was just "Message received.\n" arriving across two TCP segments,
not a real second round; corrected interpretation: 0/8 survived). Dead end.

### Where this leaves us
Working theory (moderate-high confidence, several independent lines of evidence converging):
a per-connection, dynamically-armed hardware write watchpoint on the exact runtime address
of the return-address slot, installed by something external to the binary on the remote
host only. If true, this cannot be bypassed by anything we send over the TCP byte-stream
alone (timing, splitting, raw sockets, concurrency, and content have all been tried and
fail identically) — any real bypass would need either a flaw in how/when the supervisor
re-arms the watchpoint (none found so far: no timing race, no concurrency race, no
reconnection-based staleness) or a completely different vulnerability class in this binary
that never writes to that slot directly (none found: only one write primitive exists, this
same `read()` call; the saved-RBP leak doesn't enable a pivot per finding 1's caveat).
Continuing to look for a genuinely different angle per standing instructions; this file will
be updated again as soon as anything new (positive or negative) is found.
