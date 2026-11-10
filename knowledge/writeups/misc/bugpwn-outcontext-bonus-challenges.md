---
doc_kind: writeup
title: "battleCTF Qualifier (bugpwn) — out-context bonus: Discord, 0byte, Know Your Enemy"
category: misc
slug: bugpwn-outcontext-bonus-challenges
created: 2026-11-10
status: solved
tags:
  - osint
  - discord
  - out-context
  - non-technical
source: "ctf.bugpwn.com — battleCTF Qualifier 2026"
target: "Platform Discord server + CTFd portal (no remote service/binary)"
---
# battleCTF Qualifier — out-context bonus challenges

## Challenge Summary

Three small "out context" (non-scored-category) challenges, grouped here because none involved
a real technical exploit chain — they were solved by reading the platform surface, not by
attacking anything.

## 1. Discord (id 10, 4 pts) — SOLVED

- Flag `CTF{OffWeGo}` was posted as a **pinned message in the platform's Discord server**
  (`#général`), not hidden behind any challenge logic.
- Note: the flag does **not** follow the `battleCTF{...}` format the `/rules` page states for
  the rest of the competition — an intentional one-off exception for this bonus.
- Submitted manually by the user after finding the pinned message.

## 2. 0byte (id 9, 50 pts) — SOLVED (not via technical analysis)

- Description: `Format : battleCTF{....}` (4 literal `.` bytes, confirmed via raw API fetch —
  pure ASCII, no zero-width/invisible Unicode anywhere in the challenge text, name, or `/rules`).
- An investigation thread (GitHub `AfricabattleCTF2024` lead, a `0byte.zip` from the prior year's
  edition) turned out to be a genuine lead but with **no publicly recoverable password**: Discord
  chatter (`k_c0nk`: *"I used the police station's postal code"*) confirmed the zip's password
  came from the **2024 edition's own in-game description text**, which was never public (not in
  the GitHub repo, not archived by Wayback Machine — `qualifier.bugpwn.com` only has
  unauthenticated static assets archived).
- 9 reasoned/wordplay guesses were tried and logged as incorrect
  (`battleCTF{}`, `{zero}`, `{0x00}`, `{null}`, `{vide}`, etc.) before concluding this needed an
  out-of-band lead, not more guessing.
- **Resolved outside the agent session**: the user obtained the real flag directly (likely via
  Discord DM with the organizer or a 2024-edition alumnus, per the pattern other solvers in
  `#général` described) and submitted it manually via the web UI. `solved_by_me: true` confirmed
  live, with `attempts: 9` matching exactly the 9 logged incorrect guesses — no 10th (correct)
  submission ever went through this session's tooling, confirming the final flag was entered
  directly in the browser.
- **No exploit chain to document** — this one is an honest "external source" solve, recorded here
  only so the challenge isn't silently missing from the knowledge base.

## 3. Know Your Enemy (id 17, 8 pts) — SOLVED

- No methodology captured in any workspace note — this was answered quickly enough (likely a
  one-off platform/profile/rules-page read, consistent with the category's "what do we already
  have, with zero extra lookups" theme established by the 0byte investigation) that no working
  notes were kept.
- Confirmed `solved_by_me: true` via the platform API; flag value itself was not re-captured in
  any local artifact.

## Reusable Lessons

- Not every "out context" bonus challenge is a technical puzzle — check the platform's own
  surfaces first (Discord pins, profile data, rules page, challenge name/description itself)
  before reaching for OSINT tooling. `toluene`'s own hint in Discord (*"just dont overthink guys
  fr, yall alr have everything u need"*) was accurate for this category as a whole.
- When a flag format is confirmed precisely (byte-for-byte, no hidden Unicode) but reasoned
  guesses keep failing, that is a signal to stop guessing and look for an **out-of-band** lead
  (a prior edition's archive, a community hint) rather than exhausting more wordplay — recognizing
  that boundary early saved further wasted submissions here.
- Organizers (here: RAVEN) may actively moderate spoiler-sharing in a competition Discord — don't
  expect an explicit posted answer even when players are visibly discussing a solve in real time.

## Related

- [`bugpwn-blackhole-pcap-ddos-chain`](bugpwn-blackhole-pcap-ddos-chain.md) — the other
  "out context" bonus chain from the same platform, fully technical by contrast.
