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
