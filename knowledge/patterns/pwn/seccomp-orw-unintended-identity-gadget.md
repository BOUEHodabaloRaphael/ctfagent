---
doc_kind: pattern
title: "Seccomp-Restricted Pwn: ORW Chain via Unintended Identity-Copy Gadget"
category: pwn
slug: seccomp-orw-unintended-identity-gadget
created: 2026-10-25
status: active
tags:
  - seccomp
  - rop
  - orw
  - unintended-gadget
  - pext
chain_summary: "When seccomp blocks execve/execveat and the binary has no clean pop rdi/rsi/rdx gadgets, find an unintended gadget (e.g. pext with an all-ones mask) that performs an identity register copy, then chain open/read/write syscalls via libc to read a flag file."
---
# Seccomp-Restricted Pwn: ORW Chain via Unintended Identity-Copy Gadget

## Chain Summary

- One-line chain: When seccomp blocks execve/execveat and the binary has no clean pop rdi/rsi/rdx gadgets, find an unintended gadget (e.g. pext with an all-ones mask) that performs an identity register copy, then chain open/read/write syscalls via libc to read a flag file.
- Typical target shape: small CTF pwn binary with a hand-built seccomp-bpf filter (via `prctl(PR_SET_SECCOMP, ...)`) that blocks `execve`/`execveat` (and sometimes `execveat`/`clone`/`fork`), while leaving `open`/`read`/`write`/`openat` on the allowlist by default — forcing an ORW ("open-read-write") exploitation style instead of a shell.

## Preconditions

- A memory-corruption primitive (typically a stack buffer overflow) giving ROP control, in a binary that installs a seccomp-bpf filter before the vulnerable code path runs.
- `ROPgadget`/`objdump` finds **no clean** `pop rdi;ret` / `pop rsi;ret` / `pop rdx;ret` in the binary itself (otherwise just use those directly) — common in small, hand-optimized or heavily inlined CTF binaries.
- A known or recoverable flag path string (often XOR-obfuscated and decoded by the binary's own startup code into `.bss`, avoiding the need to stage the filename string yourself).

## Cheap Probes

- Dump and manually decode the seccomp-bpf filter (`prctl(PR_SET_SECCOMP, 2, &sock_fprog)`): confirm exactly which syscall numbers hit `KILL`/`TRAP` vs. the default action. Syscall `0x3b` (execve) and `0x142` (execveat) being blocked with everything else `ALLOW` is the classic ORW setup.
- Run `ROPgadget --binary <bin> | grep -E 'pop (rdi|rsi|rdx)'`. If nothing clean turns up, widen the search to *unaligned/overlapping-instruction* gadgets and any instruction whose side effect can emulate a register move — `pext reg, src, mask` with an all-ones mask is an identity copy (`dst := src`); other candidates include `xchg`, `mov`-adjacent SIMD extract instructions, or arithmetic that reduces to a copy for a specific input.
- Check program startup banners (`printf("...%p...", code_ptr)`) for a free PIE-base leak before reaching for an overflow-based one.

## Telltale Evidence

- Seccomp filter explicitly `KILL`s `execve`/`execveat` syscall numbers while allowing everything else by default — confirms ORW is the intended (and only viable) path, not a dead end from a failed `system()`/shellcode attempt.
- `ROPgadget` returning zero results for `pop rdi;ret`-class gadgets in the binary, forcing reliance on libc gadgets for *some* registers but not others until a libc base is known.

## Escalation Order

1. Obtain a PIE-base leak (free banner leak if available, otherwise an overflow-based leak).
2. Find the unintended identity-copy gadget (e.g. `pext rdi, rax, rcx ; ret` reached by jumping mid-instruction past an unwanted leading `xor`/`clc`), and pair it with the binary's own `pop rax;ret` / `pop rcx;ret` to get full `rdi` control from binary-internal gadgets alone.
3. Use that `rdi` control plus a PLT call (e.g. `puts@plt` on a known GOT entry) to leak a libc address and compute `libc_base`.
4. With libc now mapped, use (possibly unaligned/overlapping) `pop rdi;ret` / `pop rsi;ret` / `pop rdx;ret` gadgets from libc itself for the remaining ORW chain: `open(path, O_RDONLY)` → copy the **real** returned fd into the next syscall's first argument via the same identity-copy gadget trick (never hardcode fd `3` — launcher/remote fd bookkeeping can differ from local testing) → `read(fd, scratch, len)` → `write`/`puts(scratch)`.
5. Use a leaked **stack** address as ORW scratch space, not `.bss` — small CTF binaries often pack `.bss` full of live `FILE*` globals, argv/envp copies, and obfuscated secrets; landing a write there can corrupt a `FILE*` and crash before output is produced.

## Common Mistakes

- Trying `system("/bin/sh")` or any execve-based shellcode first, instead of checking the seccomp filter up front — wastes time against a SIGSYS kill that was never going to work.
- Hardcoding a syscall's return value (like an fd) instead of capturing it live through the identity-copy gadget and threading it through — works locally, breaks silently on a different launcher/remote environment.
- Writing ORW scratch data into `.bss` without checking what's already there.
- Not retrying a canary/stack leak that terminates early (below a minimum expected length) before trusting the parsed bytes — a 1-byte-overflow-into-echo leak can occasionally under-read.
- Not cross-checking an automated protection-triage tool's PIE/NX/canary/RELRO report against raw `checksec`/`pwntools.ELF(checksec=False)` output — stdout/stderr capture bugs in custom tooling can silently invert the real picture.

## Payload Shapes

```text
# Binary-internal rdi control via identity-copy gadget (no libc needed yet)
pop_rax(binary); <value>
pop_rcx(binary); 0xFFFFFFFFFFFFFFFF   # all-ones mask -> pext becomes identity copy
pext_rdi(binary)                      # rdi := rax
<plt_call or next gadget using rdi>

# ORW chain skeleton once libc is leaked
pop_rdi(libc); <path_ptr>
pop_rsi(libc); 0            # O_RDONLY
open@libc
pop_rcx(binary); 0xFFFFFFFFFFFFFFFF
pext_rdi(binary)            # rdi := real fd from rax, not a hardcoded guess
pop_rsi(libc); <stack_scratch_addr>   # never .bss
pop_rdx(libc); <len>
read@libc
pop_rdi(libc); <stack_scratch_addr>
puts@libc / write@libc
```

## Related Writeups

- `knowledge/writeups/pwn/pwn002-vault-seccomp-orw-pext-gadget.md`

## Skill Impact

- Related skill: `pwn-triage` (binary exploitation triage/leak-strategy stage)
- Rule to add or update: when a seccomp filter is detected and blocks execve-family syscalls, immediately check for an ORW-viable `open`/`read`/`write` allowlist, and if `ROPgadget` finds no clean `pop rdi/rsi/rdx` in the target binary, widen the gadget search to unaligned/overlapping instructions for an identity-copy substitute before assuming the binary is unexploitable without a libc leak.
