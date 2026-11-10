---
doc_kind: writeup
title: "battleCTF Qualifier (bugpwn) — VULN#004 (solved, methodology not captured)"
category: misc
slug: bugpwn-vuln004-flag-only
created: 2026-11-10
status: solved
tags:
  - vuln-research
  - flag-only
  - gap-in-notes
source: "ctf.bugpwn.com — battleCTF Qualifier 2026 (challenge id 34, Vuln Research, up to 120 pts, decaying)"
target: "unrecorded — no workspace was created for this challenge"
---
# battleCTF Qualifier — VULN#004

## Challenge Summary

- Confirmed `solved_by_me: true` via the platform API (last-seen snapshot `challenges_20261028T215503Z.json`).
- **No workspace directory (`workspaces/vuln004/`) was ever created for this challenge** —
  unlike `VULN#003` and `VULN#005`, which have detailed (if incomplete) recon trails, there is
  zero local record of the target, the attached source, or any technique for this one.
- Not present in `workspaces/bugpwn/logs/submissions.log` either — the solve happened entirely
  outside this session's tracked tooling.

## Gap — Explicit, Not Guessed

- Target: **unknown**.
- Attached source/vulnerability class: **unknown**.
- Exploit steps: **unknown**.
- Flag value: **unknown** — not recorded anywhere in this repo.

This writeup exists only so the challenge isn't silently missing from the knowledge base's count
of solved `bugpwn` challenges. If the technique is still wanted, it must come from whatever
external session actually solved it.

## Reusable Lessons

- Of the 3 "Vuln Research" challenges solved on this platform, this is the one with the least
  trace — worth flagging as a process gap: even a one-line `notes.md` with the target
  IP/attachment name at the moment a challenge is first opened would have prevented a total loss
  of context here.

## Related

- [`bugpwn-vuln003-cares-cve-2020-8277`](bugpwn-vuln003-cares-cve-2020-8277.md),
  [`bugpwn-vuln005-goahead-recon-gap`](bugpwn-vuln005-goahead-recon-gap.md) — the other two
  "Vuln Research" solves on this same platform, both with at least partial recorded recon.
