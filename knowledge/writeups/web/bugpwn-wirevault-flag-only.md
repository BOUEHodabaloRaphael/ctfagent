---
doc_kind: writeup
title: "battleCTF Qualifier (bugpwn) — WireVault (solved, methodology not captured)"
category: web
slug: bugpwn-wirevault-flag-only
created: 2026-11-10
status: solved
tags:
  - flag-only
  - gap-in-notes
source: "ctf.bugpwn.com — battleCTF Qualifier 2026 (challenge id 16, web, up to 137 pts, decaying)"
target: "unrecorded — no workspace notes kept for this challenge"
---
# battleCTF Qualifier — WireVault

## Challenge Summary

- Web category challenge, confirmed `solved_by_me: true` via the platform API and the submitted
  flag in `workspaces/bugpwn/logs/submissions.log` (2026-10-09T16:24:10Z, `ok: true`).
- **No workspace directory, notes, or exploit script was created for this challenge** — unlike
  every other solve in this batch, there is no local record of the target, the vulnerability
  class, or the steps taken. This writeup exists only to avoid silently omitting a solved
  challenge from the knowledge base, and to flag the gap honestly rather than invent a plausible
  story.

## What Is Known (from the submissions log, verbatim)

```json
{"ts": "20261009T162410Z", "id": 16, "flag": "CTF{8bc0b47d16a341747a384edb8b88afb8}", "ok": true, "correct": true, "message": "Correct"}
```

No accompanying `"message"` text describing the technique (unlike most other entries in the same
log, which include a short cause note) — the submission script was likely invoked directly with an
already-known flag, meaning the actual solving happened in a different tool/session (the same
pattern seen with `PWN#Delta` and `0byte` in this batch), without a follow-up note ever being
written back into this repo.

## Flag / Outcome

- `CTF{8bc0b47d16a341747a384edb8b88afb8}`

## Gap — Explicit, Not Guessed

- Target URL/IP: **unknown** (not recorded anywhere in `workspaces/`).
- Vulnerability class: **unknown**.
- Exploit steps: **unknown**.

If the technique is still wanted for the knowledge base, it needs to come from whatever external
session/tool actually solved it (opencode notes, browser history, or the user's own memory of the
solve) — nothing here should be treated as a methodology, only as a confirmed-solved/flag record.

## Related

- [`bugpwn-ticketvault-nosql-querystring-bypass`](bugpwn-ticketvault-nosql-querystring-bypass.md),
  [`bugpwn-swiftnotes-ejs-prototype-pollution-rce`](bugpwn-swiftnotes-ejs-prototype-pollution-rce.md) —
  the two other `web`-category solves on the same platform that **do** have a full recorded chain.
