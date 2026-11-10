---
doc_kind: writeup
title: "battleCTF Qualifier (bugpwn) — PWN#001 (confirmed solved on platform; this session's own investigation never got past a suspected remote guard)"
category: pwn
slug: bugpwn-pwn001-blocked-external-solve
created: 2026-11-10
status: solved
tags:
  - rop
  - stack-canary-leak
  - gap-in-notes
  - anti-rop-guard
source: "ctf.bugpwn.com — battleCTF Qualifier 2026 (challenge id 13, pwn, up to 100 pts, decaying)"
target: "169.58.126.107:5000 — non-PIE, non-stripped vault binary; libc + loader provided"
---
# battleCTF Qualifier — PWN#001

## Challenge Summary

*"Get a shell on the remote host and read the flag."* Non-PIE, non-stripped, Full RELRO, canary,
NX `vault` binary; matching `libc.so.6`/`ld-linux-x86-64.so.2` provided. The platform confirms
`solved_by_me: true`, but **this workspace's own investigation never produced a working exploit or
flag** — it stalled at a reproducible, strange symptom and was handed off unsolved. This writeup
documents the real, reusable analysis up to that point and states the gap honestly rather than
inventing a resolution.

## Binary Structure (100% confirmed via objdump + live behavior)

- `vuln()` (`0x401220`): single 80-byte buffer at `rbp-0x50`. Two `read()`s into the same buffer —
  a 73-byte "name" (then echoed via `puts(buf)`), then the real 256-byte overflow read.
- Offsets, empirically bisected and 100% confirmed: canary at `buf+72`, saved-RBP at `buf+80`,
  saved-RIP at `buf+88`.
- `gadgets()` (`0x4011ee`) is a hand-placed ROP helper: `0x401205` = `pop rax; xchg rdi,rax; ret`
  (functions as `pop rdi;ret`), `0x401208` = bare `ret` (alignment filler) — deliberately provided
  by the challenge authors.
- Canary-leak technique: send exactly 73 non-null bytes as the name; the `puts(buf)` echo
  over-reads past them until the next real `0x00` byte, typically yielding 13 bytes (7 canary + up
  to 6 bytes of saved-RBP) — giving both the canary **and a free stack-address leak** on every
  connection, entirely through the "safe" first read (no write past offset 80 involved).

## The Reproducible Blocker

Bisection fully confirmed: an overflow that stops at exactly 88 bytes (saved-RBP fully
overwritten, return address untouched) always survives; **one byte more, touching the return
address at all, kills the connection** — deterministically, regardless of whether the written
bytes are garbage or a known-valid code pointer (`vuln`, `main`, both tried explicitly). Every
return path tried died identically (silent close right after `"Message received.\n"`, confirmed via
live `tshark` capture as a graceful FIN, not a RST):

- Direct return to `vuln`/`main`, with and without an extra `ret`-only alignment hop.
- A full `pop_rdi → puts@got → ret-align → puts@plt → main` ret2plt leak chain.
- Rate-limiting, TCP fragmentation, connection "aging", and an 8-way concurrent-connection race —
  all explicitly tested and ruled out as explanations (see below).

**Key discriminating evidence**: the exact same byte-for-byte payloads — including writing back
the *original, unmodified* return-address value — behave completely normally when replayed
**locally** against the identical binary/libc (survives, loops back to "Enter your name" as
expected), but still die **remotely** every time. Since the machine code is identical in both
environments, the difference must come from something external to the binary in the remote
deployment. Working theory (moderate-high confidence, not proven): a per-connection, dynamically
armed hardware write watchpoint (ptrace debug registers) on the exact runtime address of the
return-address slot, installed by an external supervisor — this would explain the
value-independence, the exact single-byte offset precision, and the local/remote split, all at
once. `readelf -n vault` shows no explicit CET SHSTK/IBT opt-in in `.note.gnu.property`, which
weakens (but doesn't rule out) a binary-local CET theory; a host-wide policy or external ptrace
monitor remains the leading hypothesis.

## What Was Ruled Out (reproducible negative results)

- Trailing-newline bug in the send call (confirmed and fixed: always send exact-length payloads
  with no `\n`).
- Short-canary edge case (<7 leaked bytes) — guarded against, not the cause of the crash.
- A previously-reported "split-send bypass" (sending safe bytes, then the return-address bytes in
  a second, separate send) — **retracted as a confirmed false positive**: the "surviving" bytes
  were shown to belong to the *next* round's unconsumed TCP buffer, not the protected offset.
- Rate-limiting/self-throttling from rapid reconnects — identical outcome with explicit `sleep(1)`
  and `sleep(15)` delays.
- TCP fragmentation/short reads — payloads are 96-104 bytes, far under any MTU; the deterministic
  pass/fail boundary (works ≤88, fails ≥89, every time) is inconsistent with a flaky-read theory.
- Connection "aging" (100-150 benign rounds before attempting the overflow) — the connection dies
  on its own in that range regardless of payload, an unrelated service-level cap, not leverageable.
- 8-way concurrent connections racing the same technique — 0/8 survived, no race window found.
- The saved-RBP leak enabling a stack-pivot via `leave;ret` — traced through manually: `leave`
  sets `rsp := rbp` (the **register** value at call time, unaffected by what we *write* into the
  saved-RBP memory slot), so corrupting that memory slot has no effect on the current `ret`'s
  target. Real, reusable leak primitive on its own, but not sufficient to redirect control flow.

## Gap — Explicit, Not Guessed

This workspace's handoff notes (`workspaces/pwn001/notes.md`, `HANDOFF.md`) end with **"Flag non
récupéré"** and a list of untried next steps (bisecting `gadgets()`/`vuln()` around nearby offsets
for a possible per-function address delta, recompiling locally at different optimization levels to
reproduce the observed `+0xc8` delta seen for `main()`). **The platform nonetheless shows this
challenge as solved** (`solved_by_me: true`), matching the pattern already seen with `PWN#Delta`
and `WireVault` in this same CTF: solved through a different tool/session not reflected in this
repo's own working notes. **No flag or working exploit for PWN#001 is recorded anywhere in this
workspace** — do not treat the analysis above as a complete chain, only as the real, reusable
recon that should save time if this binary (or its blocker pattern) is ever seen again.

## Reusable Lessons

- When an overflow consistently crashes a remote target only at the exact return-address boundary
  — regardless of the written value's validity — and the identical byte-for-byte test behaves
  normally locally, suspect an external supervisor/hardware watchpoint (ptrace DR0-3, CET shadow
  stack) rather than a logic error in the exploit. Confirm via packet capture that the crash is a
  graceful FIN (process exit) vs. an RST (network-level reject) to narrow the cause.
- A "split-send" timing idea that looks like a bypass should be verified by checking whether the
  "surviving" bytes actually land at the intended offset (e.g. by observing them leak back out
  in the *next* round) before trusting it — it can easily be an artifact of unconsumed buffered
  data instead of a real bypass.
- `leave; ret`'s `rsp := rbp` step uses the **register**, not the memory you can overwrite at the
  saved-RBP slot — overwriting saved-RBP's memory does not redirect the *current* function's
  return, only what RBP becomes for whatever runs next.

## Related

- [`pwn002-vault-seccomp-orw-pext-gadget`](pwn002-vault-seccomp-orw-pext-gadget.md) — the
  follow-up binary in the same series, where the identical offset map transferred directly and the
  session *did* produce a complete, confirmed exploit.
