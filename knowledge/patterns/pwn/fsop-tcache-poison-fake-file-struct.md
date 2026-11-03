---
doc_kind: pattern
title: "FSOP: tcache poisoning + safe-linking leak + fake FILE struct (bypass Full RELRO)"
category: pwn
slug: fsop-tcache-poison-fake-file-struct
created: 2026-11-03
status: active
tags:
  - pwn
  - heap
  - uaf
  - tcache-poisoning
  - fsop
  - file-stream
  - safe-linking
  - full-relro-bypass
  - glibc
chain_summary: "On glibc >=2.34 (no __malloc_hook/__free_hook), a heap UAF that leaks a pointer and lets you tcache-poison the next pointer can redirect an allocation onto _IO_2_1_stdout_; forging only the unvalidated _wide_data->_wide_vtable (not the IO_validate_vtable-protected vtable itself) to replace __doallocate with system() gets code execution on the next stream flush, with no GOT write and no care about Full RELRO."
---
# FSOP: tcache poisoning + safe-linking leak + fake FILE struct (bypass Full RELRO)

## Chain Summary

- One-line chain: On glibc >=2.34 (no __malloc_hook/__free_hook), a heap UAF that leaks a pointer and lets you tcache-poison the next pointer can redirect an allocation onto _IO_2_1_stdout_; forging only the unvalidated _wide_data->_wide_vtable (not the IO_validate_vtable-protected vtable itself) to replace __doallocate with system() gets code execution on the next stream flush, with no GOT write and no care about Full RELRO.
- Typical target shape: a heap alloc/edit/delete/show menu binary, glibc >=2.34 (`__malloc_hook`/`__free_hook` removed), no `win()` function to ret2win into, Full RELRO (rules out GOT overwrite).

## Preconditions

- A use-after-free bug reachable twice: once to leak a pointer (e.g. "show after delete" reading freed heap memory still containing a pointer), once to overwrite the freed chunk's tcache `next` pointer.
- A way to compute the libc base from the leaked pointer (e.g. an unsorted-bin-adjacent leak with a known static offset).
- Target glibc has tcache (2.26+) with safe-linking (2.32+, XORs `next` with `chunk_addr >> 12`) — you need a second leak of an in-tcache chunk's own address to recover the XOR mask before poisoning.

## Cheap Probes

- `checksec --file=binary` to confirm Full RELRO (rules out GOT-overwrite paths, points toward FSOP/vtable-adjacent techniques) and glibc version via the bundled `libc.so.6` (`strings libc.so.6 | grep "GNU C Library"` or `./libc.so.6` directly) to confirm `__malloc_hook`/`__free_hook` are gone (glibc >=2.34).
- Trigger the UAF read once and diff the output against a known heap-metadata layout to confirm pointer leakage is real, not coincidental bytes.

## Telltale Evidence

- No `win()`/`system()`-calling helper function exists in the binary (rules out simple ret2win), and GOT is read-only (Full RELRO) — these two facts together are the strongest signal that an FSOP/FILE-structure attack is the intended path rather than a GOT overwrite.
- A reachable `puts()`/`printf()`/any stream flush *after* the chunk you control has been allocated — this is the trigger point that invokes the corrupted stream's vtable/`_wide_data` machinery.

## Escalation Order

1. Leak a heap pointer via the UAF (show-after-free), compute libc base from a known static offset into that leaked value.
2. Leak the safe-linking XOR mask: free a tcache chunk, read back its (XORed) `next` pointer via the same UAF primitive, recover the mask as `next_xored ^ chunk_address`.
3. Free the target chunk again, overwrite its tcache `next` field (XORed with the recovered mask) to point at `_IO_2_1_stdout_` (or another libc `FILE` struct symbol), then allocate twice to get a pointer landing on/overlapping that structure.
4. Forge the stream fields: **leave the actual `vtable` pointer untouched/authentic** (glibc's `IO_validate_vtable` checks it's inside the known vtable region and will abort otherwise) — instead write a forged `_IO_wide_data` structure and point the `FILE`'s `_wide_data` field (offset 0xa0, unvalidated) at it. That forged struct's own `_wide_vtable` field points to a fake jump table where `__doallocate` is replaced with `system`, and the first "argument" byte position encodes a `/bin/sh\0` string the call will use.
5. Trigger any subsequent stream flush (implicit on program exit, or an explicit `puts()`/`fflush()`) — the corrupted wide-stream's allocation path calls the forged `__doallocate`, i.e. `system("/bin/sh")`.

## Common Mistakes

- Trying to overwrite the `vtable` pointer directly — this is exactly what `IO_validate_vtable` checks against a known valid range on modern glibc and will abort the program instead of calling your fake function.
- Forgetting the safe-linking XOR mask recovery step on glibc >=2.32 — tcache-poisoning a raw (non-XORed) pointer value will corrupt the heap instead of landing where intended.
- Assuming `checksec`'s global canary/RELRO report applies uniformly; always separately confirm which glibc version (and therefore which hardening — safe-linking, `IO_validate_vtable`, hook removal) is actually in play via the bundled `libc.so.6`, not assumptions from the CTF's publish date.

## Payload Shapes

```text
# pwntools-style sketch, adapt offsets to the target binary
leak1 = show(idx_after_free1)                  # heap pointer leak -> libc base
leak2 = show(idx_after_free2)                  # XORed tcache next -> recover safe-link mask
mask = leak2 ^ chunk2_addr
edit(idx_freed, p64(target_addr ^ mask))       # tcache poison, e.g. target = _IO_2_1_stdout_ addr
alloc(); alloc()                               # 2nd alloc lands on/overlaps target
edit(second_alloc_idx, fake_file_struct_bytes) # vtable field = ORIGINAL authentic value
                                                # _wide_data (offset 0xa0) = ptr to forged _IO_wide_data
                                                # forged._wide_vtable -> fake table, __doallocate = system
                                                # arg encoding = b"/bin/sh\x00" at the expected offset
# trigger: any puts()/fflush()/program-exit stream flush
```

## Related Writeups

- [AFRICC 2027 Qualifiers — full writeup](../../writeups/misc/africc2027-quals-full-writeup.md) — "secrets" (300pts, Pwn), the challenge this pattern was extracted from.

## Skill Impact

- Related skill: `pwn-triage` (`references/canary-pie.md` / `stack-overflow.md` cover ret2win/ret2libc/canary leaks but not heap/FSOP techniques yet).
- Rule to add or update: when `pwn-triage` encounters a heap menu challenge (alloc/edit/delete/show) on Full RELRO + no `win()` function, route to this pattern instead of defaulting to a GOT-overwrite assumption; worth adding a "heap/FSOP" branch to `pwn-triage`'s routing table if more heap challenges accumulate.
