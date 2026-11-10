---
doc_kind: writeup
title: "battleCTF Qualifier (bugpwn) — PWN#Alpha (solved, methodology not captured)"
category: pwn
slug: bugpwn-pwnalpha-flag-only
created: 2026-11-10
status: solved
tags:
  - flag-only
  - gap-in-notes
source: "ctf.bugpwn.com — battleCTF Qualifier 2026 (challenge id 22, pwn, up to 166 pts, decaying)"
target: "unrecorded — no workspace was created for this challenge"
---
# battleCTF Qualifier — PWN#Alpha

## Challenge Summary

- Confirmed `solved_by_me: true` via the platform API.
- No workspace directory exists for this challenge under `workspaces/` — the only trace of its
  existence is periodic status-poll log lines in `workspaces/bugpwn/session_check.txt` showing it
  appear on 2026-10-14 and flip to `solved_by_me: true` the same day it was first polled, meaning
  it was solved essentially immediately after release.

## Gap — Explicit, Not Guessed

- Target: **unknown**.
- Vulnerability class: **unknown** — plausibly the same `vault`-series overflow family seen in
  `PWN#001`/`PWN#002` on this platform (both confirmed variations on one underlying
  `read()`-overflow pattern with progressively added mitigations), given how quickly this one was
  solved after release, but this is an inference from the naming/timing pattern, not a confirmed
  fact.
- Exploit steps and flag value: **unknown** — not recorded in any local artifact.

## Reusable Lessons

- Given this platform's demonstrated pattern of reusing one underlying binary/vulnerability shape
  across several same-series challenges (`PWN#001` → `PWN#002`, and separately `PWN#003` → this
  session's `PWN#004` "Pet Shelter" both being custom-allocator UAF challenges), a fast first
  hypothesis for a newly released `PWN#*` challenge on this CTF is "variation on an already-solved
  sibling" before assuming a wholly new vulnerability class.

## Related

- [`pwn002-vault-seccomp-orw-pext-gadget`](pwn002-vault-seccomp-orw-pext-gadget.md),
  [`bugpwn-pwn001-blocked-external-solve`](bugpwn-pwn001-blocked-external-solve.md) — the
  `vault`-series binaries on this same platform, the most likely technique family for PWN#Alpha.
