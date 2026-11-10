---
doc_kind: writeup
title: "battleCTF Qualifier (bugpwn) — PWN#Delta (PowerPC binary, solved via an external tool/session)"
category: pwn
slug: bugpwn-pwndelta-powerpc-external-solve
created: 2026-11-10
status: solved
tags:
  - powerpc
  - flag-only
  - gap-in-notes
source: "ctf.bugpwn.com — battleCTF Qualifier 2026 (challenge id 18, pwn, up to 150 pts, decaying)"
target: "binary 'vault' (workspaces/pwnDelta/attachments/vault) — ELF 32-bit PowerPC, not stripped, statically linked"
---
# battleCTF Qualifier — PWN#Delta

## Challenge Summary

- Confirmed `solved_by_me: true` via the platform API. Notably **not** an x86-64 target like the
  rest of the `vault` series — this one is a 32-bit **PowerPC** ELF (`BuildID sha1
  ded868c5bd72ab766419da8c57e3e9c9e30bc0e2`), not stripped, statically linked.
- **Solved outside this agent session entirely** (the user used `opencode`, a separate tool) — no
  exploit chain, offsets, or technique is recorded anywhere in this repo.

## What Is Known

- Binary: `workspaces/pwnDelta/attachments/vault`, ELF 32-bit PowerPC, not stripped, statically
  linked — architecture alone implies the x86-64 ROP chains used for `PWN#001`/`PWN#002` on this
  same platform do **not** transfer; any real exploit here would need PowerPC-specific gadgets
  and calling convention.
- One flag submission attempt from *this* tool/session, `2026-10-09T20:31:30Z`, with flag
  `CTF{c9a9816576849a4aae690a65c1fba37d}`, failed with `ok: false` (an API/CSRF-path issue on the
  submission call itself, not necessarily a wrong-flag rejection — same ambiguous-failure pattern
  seen elsewhere in this CTF's submission log) — this attempt was abandoned in favor of the
  opencode route rather than debugged further.
- The platform later confirmed the challenge solved via that separate `opencode` session.

## Gap — Explicit, Not Guessed

- The actual vulnerability class, exploit technique, and final confirmed flag string are **not
  recorded in this repo**. If the technique is wanted for the knowledge base, it needs to come from
  the `opencode` session's own notes/solve script/flag — nothing here should be read as a
  methodology.

## Reusable Lessons

- When a CTF platform mixes architectures across a nominally single "series" of challenges (here:
  x86-64 `vault` binaries alongside a PowerPC one under a different sub-name), don't assume a
  shared technique transfers — check `file`/`readelf -h` first before reusing offsets or gadget
  addresses from a same-named sibling challenge.
- A failed automated flag submission (`ok: false`) is a prompt to check the submission mechanism
  itself (CSRF token, session cookie freshness) before concluding the flag is wrong — this
  ambiguity recurred across multiple challenges in this same CTF's submission log.

## Related

- [`pwn002-vault-seccomp-orw-pext-gadget`](pwn002-vault-seccomp-orw-pext-gadget.md) — same
  challenge-naming family on the same platform, but x86-64 and with a fully recorded chain, useful
  as a contrast for what PWN#Delta's own writeup is missing.
