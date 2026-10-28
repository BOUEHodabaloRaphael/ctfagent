---
doc_kind: pattern
title: "Custom allocator UAF: double-free without null + safe-linking bypass via known key"
category: pwn
slug: custom-allocator-selflink-fakechunk
created: 2026-10-12
status: active
tags:
  - uaf
  - double-free
  - safe-linking
  - heap
  - custom-allocator
chain_summary: "free() that forgets to NULL the handle enables repeated double-free; when safe-linking XORs with the chunk's OWN address as key (not a secret), the key is always computable, so an edit on a live alias can forge the \"next\" field and redirect the allocator to return any address (GOT for read, globals for write)."
---
# Custom allocator UAF: double-free without null + safe-linking bypass via known key

## Chain Summary

- One-line chain: free() that forgets to NULL the handle enables repeated double-free; when safe-linking XORs with the chunk's OWN address as key (not a secret), the key is always computable, so an edit on a live alias can forge the "next" field and redirect the allocator to return any address (GOT for read, globals for write).
- Typical target shape: CTF "notes"/"vault"/"inventory" style challenge with a hand-rolled size-classed slab/pool allocator sitting in front of (or instead of) glibc malloc, exposed through add/free/edit/view primitives indexed by a small fixed array of slots.

## Preconditions

- A `free`-equivalent function that does not null, invalidate, or mark-dead the caller's handle/index after freeing.
- Every other operation (edit/view/re-free) checks only "is this handle non-null", never "was this handle already freed" → unlimited UAF and double-free on the same handle.
- The allocator's freelist "next" pointer obfuscation (if any) uses a key that's derivable by the attacker — classic cases: XOR/rotate with the chunk's **own address** (as seen here: `mangle(a,b) = a XOR rol(b,13)`, called as `mangle(next, chunk_addr)`), or glibc's real safe-linking (`next XOR (chunk_addr >> 12)`) when the chunk's address is already known or cheaply leakable.
- User-facing "write into chunk" operations (add/edit) write raw, unmangled bytes — only the allocator's own free/alloc path applies the mangle, so an attacker-owned alias can inject an arbitrary encoded value.

## Cheap Probes

- Diff `free_note`/`delete`-equivalent disassembly for a missing `handle = NULL` (or `handle->valid = false`) after the free call — single most telling probe.
- Check whether the same index/handle can be freed, edited, or viewed again after being freed (no "already freed" error) — if so, UAF is trivially confirmed without any crash.
- Look for a custom `size_to_class`/pool/freelist alongside real `malloc`/`free` fallbacks for larger sizes — common pattern when challenge wants to dodge glibc tcache protections while still giving you a real-heap path for an unsorted-bin/libc leak.

## Telltale Evidence

- `free()` function body: pushes to a freelist/stack but never rewrites the original pointer/array slot that referenced the chunk.
- A `mangle`/`protect_ptr`-style helper that takes the chunk's own address as one operand — if a decompiled/disassembled version shows `key = chunk_addr` (not a per-process secret, not `&tcache_struct`), the whole safe-linking scheme is bypassable with zero extra leak once you know any one chunk's address.
- `view`/`print`/`display`-style operations that call a stored function pointer (vtable/formatter pattern) with a stored data pointer — a prime overwrite target once arbitrary write is available (more ergonomic than trying to defeat Full RELRO's GOT protection).

## Escalation Order

1. Confirm the missing-null bug: free the same handle twice, or free then view/edit, and see stale/freed data come back without error.
2. Get one chunk's exact address for free: free a handle for the *first time ever in its size class* (so the freelist's "previous head" is 0/NULL), then UAF-view it. The raw stored bytes equal `mangle(0, chunk_addr)`, which inverts to `chunk_addr` directly (e.g. `ror(leak, 13)` for a `rol(.,13)` scheme).
3. Build the minimal "self-loop" double-free: free the *same* chunk twice in a row (no second chunk needed). Its stored bytes become `mangle(chunk_addr, chunk_addr)`, which always decodes back to itself — so the freelist head keeps resolving to this one chunk no matter how many times it's popped, until you change its bytes.
4. Pop it once (legitimately own it via a fresh handle), raw-edit its first 8 bytes to `target_addr XOR rol(chunk_addr, key_rotate)` (or whatever the mangle formula's inverse is), pop again (decodes to `target_addr`, becomes new freelist head), pop a third time → the allocator hands back `target_addr` as a "freshly allocated" chunk. The very next user-controlled write into that "allocation" is an arbitrary-address write.
5. Pick write targets inside the binary's own writable globals first (a stored content-pointer field, a stored function-pointer/vtable slot) before reaching for GOT — Full RELRO blocks GOT *writes* but not *reads*, so: (a) use the primitive to overwrite a note's own "content pointer" field with a GOT address, then use the normal `view` to leak the real resolved function address (works even under Full RELRO); (b) use the primitive a second time (same chunk, just re-free it twice more to re-arm the self-loop — no fresh allocation needed) to overwrite a stored function pointer with `system`'s computed address, with the paired data pointer already seeded with `"/bin/sh"`.
6. Identify the exact libc build from 2+ leaked real function addresses via `https://libc.rip/api/find` (POST `{"symbols": {"fn1": "0x...", "fn2": "0x..."}}`), filter out mismatched-arch candidates (`i386`/`i686`/`x32` substrings) in the response, then compute `system = libc_base + system_offset`.
7. Trigger the hijacked function pointer with its paired data pointer to get code execution (`system("/bin/sh")` or equivalent).

## Common Mistakes

- Assuming a double-free needs two distinct chunks — a single chunk freed twice in a row ("self-loop") is cheaper and needs no second allocation.
- Burning allocation slots/handles carelessly — each handle in this family of challenges is usually a **non-renewable resource** (add on an already-non-null handle is refused, and free never nulls it, so a handle can never be "added" again after its first use). Budget every `add`/`alloc` call before writing the exploit; re-free an already-dangling handle (free_note-equivalent) and re-edit it instead of allocating a fresh one wherever possible.
- Trying to overwrite GOT entries directly when Full RELRO is active — this merely crashes the target (GOT page is read-only). Use GOT only as a *read* leak target; write to the binary's own writable data instead.
- Identifying libc from a single leaked symbol — `libc.rip` (and similar databases) can return a wrong, even wrong-architecture, top match on a single address; always leak 2+ symbols and sanity-filter the architecture string.
- Trusting a repo's own automated protection-checker (`pwn_check.py` or similar) without cross-checking against `pwntools.ELF(...).pie/.nx/.canary/.relro` (ground truth) before committing to a strategy — a wrong read (e.g. "PIE/NX/canary disabled" on an actually PIE+NX+canary+Full-RELRO binary) sends you down an impossible exploitation path.
- Using a `dlopen()`'d copy of a candidate libc to precompute offline offsets (e.g. unsorted-bin-to-arena-base) — a dynamically `dlopen`'d libc often initializes a secondary/mmap'd arena instead of the normal brk-based main arena, giving offsets that don't match a normally-linked process. Prefer a live leak + online identification (libc.rip) over offline precomputation from an unverified local copy.

## Payload Shapes

```python
# core primitive: turn the custom allocator into an arbitrary-address allocator
def fake_chunk_write(io, a_addr, holder_idx, pop1_idx, pop2_idx, pop3_idx, target_addr, payload):
    free(io, holder_idx)
    free(io, holder_idx)                       # double free -> self-loop on chunk A
    add(io, pop1_idx, SZ, b"p1")                 # pop A, legitimately own it
    forge = target_addr ^ rol(a_addr, KEY_ROT)
    edit(io, pop1_idx, p64(forge))               # raw overwrite, no mangle applied to user writes
    add(io, pop2_idx, SZ, b"p2")                  # pop A again -> freelist head = target_addr
    add(io, pop3_idx, len(payload), payload)      # pop target_addr, write payload there

# recovering a chunk's own address from its first-ever free + UAF view
chunk_addr = ror(u64(leaked_bytes[:8]), KEY_ROT)   # since prev_head was NULL at first free
```

## Related Writeups

- [[pwn003-notes-uaf-fakechunk]] — bugpwn.com PWN#003, full derivation and working exploit script.

## Skill Impact

- Related skill: `pwn-triage` (routing: add "custom allocator / notes-style UAF" branch alongside canary-pie and stack-overflow), and `src/tools/pwn/pwn_check.py` (bug: misreported PIE/NX/canary/RELRO on a real PIE+NX+canary+FullRELRO binary — needs a fix or at least a "cross-check with pwntools" warning before this tool's output is trusted for strategy selection).
- Rule to add or update: in `pwn-triage`, add an explicit step to re-verify protections with `pwntools.ELF(checksec=False)` before trusting any custom checker, and a decision branch for "custom size-classed allocator with array-indexed handles" pointing at this pattern instead of only canary-pie/stack-overflow.
