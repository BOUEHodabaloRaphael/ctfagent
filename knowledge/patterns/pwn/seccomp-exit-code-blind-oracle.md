---
doc_kind: pattern
title: "Seccomp bypass via exit-code blind oracle"
category: pwn
slug: seccomp-exit-code-blind-oracle
created: 2026-11-03
status: active
tags:
  - pwn
  - seccomp
  - rop
  - exit-code-oracle
  - blind-exfiltration
  - alloca-overflow
chain_summary: "When a seccomp filter kills every output syscall (write/send*/splice/...) but the harness/service exposes process exit code or success/failure as an observable signal, a ROP chain that compares target data byte-by-byte against a guessed value and calls exit_group(match) turns an unexfiltratable overflow into a remote, brute-forceable boolean oracle."
---
# Seccomp bypass via exit-code blind oracle

## Chain Summary

- One-line chain: When a seccomp filter kills every output syscall (write/send*/splice/...) but the harness/service exposes process exit code or success/failure as an observable signal, a ROP chain that compares target data byte-by-byte against a guessed value and calls exit_group(match) turns an unexfiltratable overflow into a remote, brute-forceable boolean oracle.
- Typical target shape: a static/stripped-of-PIE SUID or server-side binary with a controllable stack/buffer overflow (e.g. `alloca()`-based) and its own `seccomp` filter installed in `main()`, running behind a harness that exposes only the process's exit status (web app checking `returncode == 0`, a scoring script, a wrapper that prints "success"/"failure").

## Preconditions

- A working overflow primitive that gives ROP/control-flow hijack (overflow itself must already be solved/confirmed before this applies).
- `seccomp-tools dump ./binary` (or manual BPF filter disassembly) shows all data-exfiltration syscalls (`write`, `send*`, `sendfile`, `splice`, `copy_file_range`, etc.) are killed, while `exit`/`exit_group` and typically `open`/`read` (or equivalent) remain allowed.
- The harness/service around the binary surfaces the process's exit code or an equivalent binary success/failure signal to the attacker (directly, via an HTTP status, or via a log/response difference).

## Cheap Probes

- `seccomp-tools dump ./binary` — fastest way to get the exact killed-syscall list; if it's unavailable, `strace -f ./binary` locally (if runnable) and watch for `SIGSYS` on specific syscalls, or disassemble the `prctl(PR_SET_SECCOMP, ...)` BPF program manually.
- Try a normal `write()`-based ROP shell/leak first anyway — if it silently produces no output despite a correct chain (and `SIGSYS`/core-dump is visible when run unprivileged locally), that confirms the seccomp block rather than a chain-construction bug.
- Confirm the harness actually surfaces exit code: run the binary locally with different `exit()` codes and check whether the wrapping service's response/log changes accordingly.

## Telltale Evidence

- `perror()`/any libc call that implicitly does a `write(2, ...)` under the hood triggers a crash/core-dump when run unprivileged, even though the "logic" leading to it is correct — confirms seccomp is killing the write, not that the exploit chain itself is wrong.
- The harness response or scoring distinguishes `exit_group(0)` from any non-zero exit in an observable way (different HTTP status, different message, different log line) — this is the oracle channel.

## Escalation Order

1. Confirm the overflow primitive gives full ROP control independent of the seccomp issue (e.g. test locally without the filter, or reason purely from the disassembly).
2. Enumerate exactly which syscalls remain usable post-seccomp: typically `open`/`read`/`mmap`/`exit_group` survive even aggressive filters, since they don't exfiltrate data by themselves.
3. Build a ROP chain that: (a) reads the target secret (e.g. `/flag`) into a writable buffer via `open`+`read`; (b) compares one byte of that buffer against an attacker-supplied guess (passed as an argument or pre-staged on the stack); (c) calls `exit_group(result)` where `result` is 0 only if the guessed byte matches.
4. Script the brute force externally: for each byte position, try candidate values (full byte range, or a narrowed charset like `[a-zA-Z0-9_{}!]` for CTF flag formats) and observe the harness's success/failure signal per attempt; move to the next position once a match returns success.
5. Budget request count realistically before committing: byte-range brute force is ~128-256 requests/char depending on charset; for long secrets, consider a smarter comparison (binary search on byte value via `<`/`>` comparisons in the ROP chain, if a 3-way branch is feasible) to cut requests per char roughly in half-to-quarter via `log2(charset_size)` instead of linear scan.

## Common Mistakes

- Giving up on a seccomp-blocked overflow as "unexploitable" instead of checking what the surrounding harness exposes as an observable side channel (exit code, timing, response size, error-message variant).
- Forgetting that even an allowed `read()` syscall doesn't help if there's no way to branch on its result and reach a distinguishable `exit_group()` call — the oracle requires the ROP chain to encode a comparison, not just a read.
- Linear single-byte brute force when the comparison primitive actually supports ordering (`<`,`>`,`==`) — missing an opportunity to binary-search each byte and cut the request budget significantly.

## Payload Shapes

```text
# ROP chain sketch (syscall numbers/gadget addrs are target-specific)
open("/flag", O_RDONLY) -> fd
read(fd, buf, N)
cmp buf[i], guessed_byte
exit_group( buf[i] == guessed_byte ? 0 : 1 )   # or encode as a conditional-move into the exit code
```

```bash
# external brute-force driver sketch
for i in range(flag_len_guess):
    for c in charset:
        send_overflow_with(index=i, guess=c)
        if remote_returns_success():
            flag += c
            break
```

## Related Writeups

- [AFRICC 2027 Qualifiers — full writeup](../../writeups/misc/africc2027-quals-full-writeup.md) — "bmpcheck" (200pts, Pwn), the challenge this pattern was extracted from.

## Skill Impact

- Related skill: `pwn-triage` (`references/initial-recon.md` should include a seccomp check step if it doesn't already — `seccomp-tools dump` or equivalent belongs in the standard recon checklist alongside `checksec`).
- Rule to add or update: when `pwn_check.py`/initial recon detects a seccomp filter blocking all write-family syscalls, explicitly prompt for "what does the harness expose as an observable signal?" (exit code, timing, response diff) before concluding the challenge needs a different primitive entirely.
