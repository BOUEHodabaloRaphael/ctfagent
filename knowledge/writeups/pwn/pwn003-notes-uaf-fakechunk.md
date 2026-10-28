---
doc_kind: writeup
title: "PWN#003 - Custom Notes Allocator UAF to system(\"/bin/sh\")"
category: pwn
slug: pwn003-notes-uaf-fakechunk
created: 2026-10-12
status: solved
tags:
  - uaf
  - double-free
  - safe-linking
  - fake-chunk
  - arbitrary-write
  - got-leak
  - libc-rip
  - function-pointer-hijack
source: "bugpwn.com (battleCTF Qualifier)"
target: 169.58.126.107:5002
---
# PWN#003 - Custom Notes Allocator UAF to system("/bin/sh")

## Challenge Summary

- Source: bugpwn.com (battleCTF Qualifier), CTFd challenge id 20, 144 pts
- Target: 169.58.126.107:5002
- Goal: "Get a shell on the remote host and read the flag." One attached ELF (`notes`, PIE, NX, canary, Full RELRO, not stripped of useful symbols).

## Initial Signals

- Entry point: `notes` menu with 1) Add 2) Free 3) Edit 4) View 5) Exit, 8 note slots (index 0-7).
- Visible hints: a gratuitous `[debug] build id: %p` line printed at startup, leaking `&main` — an intentional PIE-base giveaway.
- First confirming probe: `pwn_check.py` claimed PIE/NX/canary disabled and RELRO none. **This was wrong** — ground truth via `pwntools.ELF(checksec=False)` showed PIE=True, NX=True, Canary=True, RELRO=Full. Always re-verify protections with pwntools directly when the result changes the exploitation strategy; see pattern note.

## Exploit Chain

1. Statically analyzed the custom allocator: 3 size classes (32/64/128 bytes) backed by one `malloc(0x4000)` pool; `size_to_class(size)>128` falls back to real `malloc`/`free`. Freed chunks are pushed onto a per-class singly-linked `freelist[]`, with the "next" pointer obfuscated via `mangle(a,b) = a XOR rol(b,13)`, keyed on **the chunk's own address** (not a secret, not randomized per-process beyond normal heap ASLR).
2. Root bug: `free_note()` never sets `notes[idx] = NULL`. Every operation (`free`, `edit`, `view`) only checks `notes[idx] != NULL`, never "is this still valid" → unlimited UAF / double-free on any index.
3. **Self-loop double-free primitive**: freeing the *same* index twice in a row (no second chunk needed) makes the chunk encode `mangle(own_addr, own_addr)`, which decodes back to itself forever — i.e. `freelist[class]` keeps resolving to the same chunk no matter how many times it's popped, until its raw bytes are changed.
4. Because `edit_note`/`add_note`'s body write is a **raw, unmangled** `read()` into the chunk, and the chunk's "key" for `mangle` is just its own (known) address, we can pop the chunk once (own it legitimately), overwrite its first 8 bytes with `target_addr XOR rol(chunk_addr,13)`, then pop it again: the allocator decodes our forged value and sets `freelist[class] = target_addr`. One more pop makes `content_alloc()` return `target_addr` directly, and the immediately-following `add_note` body write deposits our bytes **at that arbitrary address** — a 4-`add_note`-call (1 initial alloc + 2 "free" + 3 pops, see pattern note for exact count) arbitrary-write primitive, independent of any heap leak (the key is derivable once you know *one* chunk's address, itself obtained the same way: free once, view via UAF, the raw bytes are `rol(own_addr,13)` since the "previous head" was NULL).
5. Full RELRO blocks a GOT **write**, but not a GOT **read**. Redirected the write primitive at `notes_storage[0].content` (one note's own content-pointer field, not a GOT entry) to equal `&printf@got`, then called `view(0)`: `default_formatter` does `write(1, content, 0x20)`, dumping the *real* GOT-resolved addresses of `printf`, `read`, `strtol`, `malloc` (0x20 bytes = 4 adjacent GOT slots at this binary's layout).
6. Queried `https://libc.rip/api/find` with all 4 leaked symbols → exactly one candidate, `libc6_2.42-13_amd64`. (A query with only `printf` returned a wrong i386 2.26 build — always leak/submit 2+ symbols and filter out non-matching arch strings.) Computed `system()`'s real address from the match.
7. Repeated the same fake-chunk write (reusing the same physical chunk via its still-dangling alias index, re-freeing it twice to re-establish the self-loop — no new heap chunk needed) to overwrite `notes_storage[7].formatter` (a per-note function pointer called by `view_note`) with `system`'s address. `notes_storage[7].content` had already been set, by a normal `add_note` done at the very start, to a buffer holding `"/bin/sh\0"`.
8. `view(7)` → binary executes `notes[7]->formatter(notes[7]->content)` == `system("/bin/sh")` → shell as `uid=65534(nobody)`.
9. `find / -iname '*flag*'` → `/flag/flag.txt` → `cat` → flag.

## Key Evidence

- `size_to_class`/`palloc`/`pfree`/`mangle` disassembly showed the exact XOR/rotate formula and that the "key" is the chunk's own address (not a global secret) — this is what makes the bypass possible without any extra heap leak.
- `free_note` disassembly: no `notes[idx] = 0` after `content_free()` — the single root cause.
- `readelf -r` confirmed `printf@GLIBC_2.2.5` GOT slot at offset `0x3fa8`; GOT layout order (free, puts, write, __stack_chk_fail, printf, read, strtol, malloc, setvbuf, exit, __libc_start_main, ...) let one 0x20-byte leak cover 4 real function addresses at once.

## Dead Ends

- `pwn_check.py`'s protection report (PIE/NX/canary disabled, RELRO none) was flat-out wrong for this binary; trusting it would have led to a (wrong) ret2shellcode/GOT-overwrite plan that Full RELRO + NX would have blocked. Re-verified with `pwntools.ELF` before committing to a strategy.
- Tried a local `dlopen()`-based probe against a candidate `libc.so.6` (reused from another workspace) to precompute an unsorted-bin-to-libc-base offset; the `dlopen`'d copy created a secondary/mmap'd arena instead of the normal brk-based main arena, so the "leak" didn't correspond to a real main-arena offset. Abandoned in favor of a direct, named-symbol GOT leak + libc.rip identification, which needs no offline libc copy at all.
- First `libc.rip` query used only the `printf` leak and returned a spurious 32-bit (`i386`) candidate as the top result — a single symbol is not enough to disambiguate; always send multiple leaked symbols and discard non-matching architectures.

## Payloads And Commands

Full working exploit: `workspaces/pwn-003/exploit/exploit.py` (self-contained, pwntools). Key primitive:

```python
def fake_chunk_write(io, a_addr, holder_idx, pop1_idx, pop2_idx, pop3_idx, target_addr, payload):
    free(io, holder_idx)
    free(io, holder_idx)                      # double free -> self-loop on chunk A
    add(io, pop1_idx, 32, b"p1")               # pop A, legitimately own it
    forge = target_addr ^ rol(a_addr, 13)
    edit(io, pop1_idx, p64(forge))             # raw overwrite of A's "next" field (no mangle on user writes)
    add(io, pop2_idx, 32, b"p2")                # pop A again -> freelist head = target_addr
    add(io, pop3_idx, len(payload), payload)    # pop target_addr, write payload there
```

Recovering a chunk's own address from a single free + UAF view (first free ever for that class, so "previous head" = NULL):

```python
enc = u64(leaked_bytes[:8])          # == rol(chunk_addr, 13)
chunk_addr = ror(enc, 13)
```

## Flag / Outcome

- Flag: `CTF{0b1578aa1b39f4c6ab9a857a657ee71a}`
- Submitted via CTFd API (`/api/v1/challenges/attempt`, challenge id 20) → `{"status": "correct"}`, +144 pts.

## Reusable Lessons

- Re-verify binary protections with `pwntools.ELF(checksec=False)` (or `checksec` CLI) before trusting any custom triage tool's output — a wrong PIE/RELRO/NX read changes the whole exploitation strategy.
- A `free()` that doesn't null the caller's handle is a UAF/double-free regardless of any pointer-mangling scheme layered on top, *if* the mangling key is derivable (e.g. the chunk's own address) rather than a真 secret.
- Full RELRO stops GOT writes but not GOT reads — a read-only arbitrary-read primitive can still fully deanonymize libc via GOT if the target binary calls enough libc functions to leak.
- `libc.rip` needs 2+ leaked symbols to avoid false-positive cross-arch matches; one symbol alone is not reliable.
- Reusing another workspace's `libc.so.6` via `dlopen()` for offline offset-probing is unreliable (secondary arena, not brk-based main arena) — prefer a direct named-symbol leak from the live target + libc.rip over precomputing offsets from an unverified local copy.

## Pattern Candidates

- New pattern created: `knowledge/patterns/pwn/custom-allocator-selflink-fakechunk.md`
