---
doc_kind: writeup
title: "PWN#002 Vault - PIE + Seccomp Stack Overflow, ORW Chain via Unintended pext Gadget"
category: pwn
slug: pwn002-vault-seccomp-orw-pext-gadget
created: 2026-10-25
status: solved
tags:
  - seccomp
  - orw
  - rop
  - pie-leak
  - canary-leak
  - unintended-gadget
  - pext
  - no-clean-gadgets
source: "bugpwn.com (battleCTF Qualifier)"
target: 169.58.126.107:5001
---
# PWN#002 Vault - PIE + Seccomp Stack Overflow, ORW Chain via Unintended pext Gadget

## Challenge Summary

- Source: bugpwn.com (battleCTF Qualifier), CTFd challenge "Vault", 135 pts
- Target: `169.58.126.107:5001`, binary `vault` (PIE, stripped, Full RELRO, canary, NX, glibc 2.42) with a hand-built seccomp-bpf filter blocking `execve`/`execveat`
- Goal: Get a shell/flag via a stack overflow, but with no `execve`-based path available — the intended solution is a direct open/read/write (ORW) syscall chain to read `/flag/flag.txt`

## Initial Signals

- Entry point: a "Deep Vault Terminal" menu that prompts for a "name" and prints `"Vault seal: %016lx"` with a live code pointer before any interaction — an unprompted leak offered up front.
- Visible hints: the binary is stripped but structurally identical (same buffer offsets, same two-`read()` pattern, same echo-back) to a non-stripped/non-PIE sibling challenge "PWN#001", making static analysis much faster by comparison.
- First confirming probe: the repo's own `pwn_check.py` triage tool reported **every** protection (PIE/NX/canary/RELRO) as disabled — flat-out wrong; `pwn_check.py` only captures `checksec`'s `stdout`, but pwntools logs its report to `stderr`. Raw `checksec --file=` (or `pwntools.ELF(checksec=False)`) is required before trusting any protection assessment from this tool.

## Exploit Chain

1. **Free PIE-base leak.** The startup banner `"Vault seal: %016lx"` prints the runtime address of `main+0x11` unprompted: `pie_base = leaked_value - 0x13a6`. No overflow needed for this step.
2. **Canary + partial stack leak via a 1-byte overflow.** The "name" prompt does `read(0, buf, 0x49)` (73 bytes) into a buffer sitting exactly 72 bytes before the stack canary, whose low byte is always `0x00` by design. Sending **72 filler bytes + 1 extra byte** overwrites that null LSB with a non-null value; the subsequent `"Hello, " + puts(buf)` echo then prints past the now-non-null-terminated canary until it hits the *next* real `0x00` byte — leaking canary bytes 1-7, the saved RBP, and part of the saved return address in one shot (`real_canary = b'\x00' + leaked[0:7]`). The over-read occasionally terminates early (0-1 real RBP bytes); retry until the leak is at least 12 bytes before trusting the parsed RBP.
3. **Stage 1 — leak libc via ret2plt using only binary-internal gadgets.** ROPgadget finds no clean `pop rdi`/`pop rsi`/`pop rdx` in the binary, but there is a clean `pop rax;ret` and `pop rcx;ret`, plus one very useful **unintended gadget**: jumping mid-instruction into `clc; xor eax,eax; pext rdi,rax,rcx; ret` (skipping the leading `xor`) lands directly on `pext rdi, rax, rcx ; ret`. With `rcx = 0xFFFFFFFFFFFFFFFF` (all-ones mask), `pext` becomes an **identity copy**: `rdi := rax`. Combined with the binary's own `pop rax;ret`/`pop rcx;ret`, this gives full `rdi` control from binary-internal gadgets alone, before any libc address is known: `pop_rax(PUTS_GOT); pop_rcx(0xFFFF...FFFF); pext_rdi; puts@plt` leaks `puts@libc`, then returns cleanly back into the vulnerable prompt for a second round. `libc_base = leaked_puts - libc.symbols['puts']`.
4. **Stage 2 — ORW chain to read and print the flag.** With libc gadgets now available (unaligned/overlapping `pop rdi;ret`, `pop rsi;ret`, `pop rdx;ret`), the second `read(0, buf, 0x100)` prompt is overflowed with a chain that: opens `FLAG_PATH` (which the binary itself decodes at startup from an XOR-obfuscated `.bss` blob, key `0x5a`, into `/flag/flag.txt` — no need to stage the filename string), copies the **real** returned fd into `rdi` via the same `pop_rax`/`pop_rcx`/`pext_rdi` trio (hardcoding fd `3` works locally but fails silently on the remote target, which has different fd bookkeeping in its launcher), reads the file contents into a **stack** scratch address (not `.bss`, which is "full" of live `FILE*` globals/argv/envp copies/the XOR ciphertext — landing on `stdout`'s `FILE*` corrupts it and crashes the next `puts`), then calls `puts` on the result.
5. Flag printed directly in the response.

## Key Evidence

- `prctl(PR_SET_NO_NEW_PRIVS,1)` then `prctl(PR_SET_SECCOMP,2,&sock_fprog)` confirmed at `fcn.000012b1`; manually decoding the 5-instruction BPF filter shows it only `JEQ`-matches syscall numbers `0x3b` (execve) and `0x142` (execveat) → `KILL`, default `ALLOW` — confirms `open`/`read`/`write` are explicitly permitted and execve-based shells are categorically dead.

## Dead Ends

| Pitfall | Fix |
|---|---|
| `system("/bin/sh")` or any execve-based shell | Killed by seccomp (SIGSYS). Use open/read/write instead. |
| Hardcoding `open()`'s return fd as `3` | Worked locally, failed silently on remote (different fd bookkeeping in the launcher). Fixed by capturing the *real* `rax` right after `open()` and copying it into `rdi` via the `pop_rax`/`pop_rcx`/`pext_rdi` trio. |
| Writing the `read()` scratch buffer into `.bss` | That region is "full" (stdin/stdout/stderr `FILE*` globals, argv/envp copies, XOR ciphertext, decoded flag path). Landing on `stdout`'s `FILE*` corrupts it and crashes on the next `puts`. Fixed by using a leaked **stack** address (`rbp - 0x400`) as scratch instead. |
| Trusting short canary/RBP leaks (`len < 12`) | Retry the leak step until at least 12 bytes come back. |
| Trusting `pwn_check.py`'s protection report | It reported every protection disabled — a bug in the tool (stdout-only capture), not the binary. Always cross-check with raw `checksec`/`pwntools.ELF`. |

## Payloads And Commands

```python
# Stage 1: binary-internal rdi control via unintended pext identity-copy gadget
pop_rax(binary); PUTS_GOT
pop_rcx(binary); 0xFFFFFFFFFFFFFFFF
pext_rdi(binary)                        # rdi := rax == &puts@got
puts_plt
ret_to_loop(pie_base + 0x148a)          # clean re-entry into the next round

# Stage 2: ORW chain using libc gadgets + the same pext trick for the real fd
pop_rdi(libc); FLAG_PATH
pop_rsi(libc); 0
open_libc
pop_rcx(binary); 0xFFFFFFFFFFFFFFFF
pext_rdi(binary)                        # rdi := rax == real fd (NOT hardcoded 3!)
pop_rsi(libc); SCRATCH_STACK            # a leaked stack address, never .bss
pop_rdx(libc); 0x60
read_libc
pop_rdi(libc); SCRATCH_STACK
puts_libc
```

## Flag / Outcome

- Flag: `CTF{e0a79830f06dca87a52f8be6d895deae}`
- Exploit reproducible against the remote target (full script referenced as `workspaces/pwn002/exploit.py` in the CTFAgent repo).

## Reusable Lessons

- A `printf("...%016lx...", some_code_pointer)` startup banner is a free PIE-base leak — always check program banners before reaching for an overflow-based leak.
- Stack canaries always have a `0x00` low byte by design; a 1-byte overflow overwriting *exactly* that byte, followed by a string-echo, leaks everything up to the next real null byte — easy to miss in an obfuscated/flattened state machine.
- When ROPgadget finds no clean `pop rdi/rsi/rdx`, check its *unaligned/overlapping-instruction* results for gadgets that achieve the same effect through an unrelated instruction — here, `pext` with an all-ones mask is an identity register copy.
- Treat `.bss` as fully occupied in small hand-rolled CTF binaries — prefer a leaked stack address as ROP scratch space over guessing at a "free" `.bss` offset.
- Never hardcode a syscall's return value (like a file descriptor) when it can instead be captured live and threaded through the chain — local/remote launcher differences can silently break a hardcoded assumption.

## Pattern Candidates

- New pattern created: `knowledge/patterns/pwn/seccomp-orw-unintended-identity-gadget.md`
