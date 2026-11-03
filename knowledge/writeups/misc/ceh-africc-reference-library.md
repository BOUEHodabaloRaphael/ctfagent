---
doc_kind: writeup
title: "CEHv13 + AFRICC reference library (21 modules + links)"
category: misc
slug: ceh-africc-reference-library
created: 2026-11-03
status: reference
tags:
  - reference
  - ceh
  - cheat-sheet
  - web
  - pwn
  - crypto
  - recon
  - wireless
  - iot-ot
  - cloud
  - malware
  - social-engineering
  - nctf26
source: "EC-Council CEHv13 (OCR, Downloads/CEH) + AFRICC CTF training slides"
target: "N/A (reference library, not a solved challenge)"
---
# CEHv13 + AFRICC reference library (21 modules + links)

## Challenge Summary

- Source: 22 EC-Council CEHv13 PDFs (scanned/image-only, OCR'd page by page with
  `pdftoppm` + `tesseract`) and 3 AFRICC CTF-training PPTX decks, all found in
  `~/Downloads/CEH/`.
- Target: N/A — this is not a solved challenge, it is a pre-event reference
  library built ahead of NCTF26 (opens Fri 2026-11-06 19:00 Lomé) at the
  user's request ("insère les techniques dans notre préparation du CTF").
- Goal: have condensed, actionable technique sheets (payloads/commands/tools,
  not exam theory) ready to consult mid-challenge instead of re-deriving
  attacks from scratch during the event.

## Initial Signals

- Entry point: user pointed at `~/Downloads/CEH/` and a SpecterOps blog post
  (LDAP signing bypass / NTLM relay), asked to read everything "très en détail"
  and feed it into the Friday CTF prep.
- Visible hints: the 22 CEH PDFs render as pure watermark text under
  `pdftotext` (`hide01.ir` repeated char by char) — confirms they are
  scanned/image PDFs, not text PDFs. OCR via `pdftoppm -r 150 -gray -png`
  (whole PDF in one call) then `tesseract` is the only extraction path.
- First confirming probe: rendering one page and running plain `tesseract`
  showed pages legitimately take 90-110s (dense pages up to ~259s), but a
  wrong watchdog kill-threshold (90s, later 240s) was initially mistaken for
  "pathological pages" being the problem.

## Exploit Chain

(N/A in the usual sense — this section instead documents the **production
pipeline** built to extract the library, since the pipeline itself is the
reusable artifact for any future large-OCR knowledge job.)

1. `pdftoppm -r 150 -gray -png "<pdf>" <scratchpad>/mNN/page` — render every
   page of a module in **one** call (much faster than page-by-page).
2. OCR each PNG with `tesseract` in parallel via `xargs -P 2` (or `-P 4` when
   running solo), **always prefixed with `OMP_THREAD_LIMIT=1`** (see Key
   Evidence — this was the actual bottleneck, not slow/broken pages).
3. Delete each PNG right after its OCR to keep disk usage bounded.
4. Concatenate the module's `.txt` pages in order, extract only offensive
   techniques/payloads/commands/tools/probe-order/pitfalls (explicitly
   dropping exam theory and long verbatim transcription — this was clarified
   mid-task after an early draft was too close to a raw OCR dump), and write
   one condensed Markdown file per module to `knowledge/ceh/mNN-*.md`.
5. For AFRICC: unzip each `.pptx` (it's a zip container), grep
   `ppt/slides/*.xml` + `_rels/*.xml.rels` for `https?://` links, dedupe, fetch
   each with WebFetch, and write `knowledge/ceh/africc-links.md`.
6. Wire the result into the *solving* path, not just storage: added pointers
   to the relevant `knowledge/ceh/mNN-*.md` files inside `web-triage`,
   `pwn-triage`, `rev-triage` (`SKILL.md`) and
   `ctf-solver-profile/references/category-switches.md`, plus a condensed
   cross-category cheat sheet at
   `workspaces/nctf26/prep-ceh-africc-cheatsheet.md` that the NCTF26 launch
   protocol (`workspaces/nctf26/notes.md` step 2) now re-reads automatically.

## Key Evidence

- `page-18.png` (one of several pages that looked "stuck"/killed by the
  watchdog at every threshold tried: 90s, then 240s, then 320s): plain
  `tesseract page-18.png out -l eng` hung past 60s repeatedly; with
  `OMP_THREAD_LIMIT=1 tesseract page-18.png out -l eng` it finished in **9s**
  with good text. Root cause: tesseract spawns OpenMP threads equal to core
  count *per process*; with 2+ parallel workers on a 4-core box, severe
  thread oversubscription looks exactly like a hang, at any kill-threshold.
- `pipeline_progress.log` entries (`[m20] OCR_DONE (258 pages)`, `[m14] OCR_DONE
  (368 pages)`, `PIPELINE_ALL_DONE`) and final page-count checks
  (`ls <scratchpad>/mNN/*.txt | wc -l` matching each module's real page count,
  e.g. m19: 342/342, m07: 268/268) are what confirmed each module as complete
  before writing its Markdown — not the subagents' own self-reported status,
  which was repeatedly stale/optimistic across this session.

## Dead Ends

- Page-by-page sequential `pdftoppm` + `tesseract` (no batching): far too slow
  (~1 page/2min), would have taken 15-24h for the first 4 modules alone.
- Watchdog killing any `tesseract` process past 90s, "to catch pathological
  pages": wrong diagnosis — killed ~60 *normal* pages on M11 alone (their PNGs
  were also deleted by the OCR wrapper's `rm -f` on kill, forcing a
  re-render). Raising the threshold to 240s, then 320s, still didn't fix
  throughput — only `OMP_THREAD_LIMIT=1` did.
- Two OCR pipelines running in parallel (2 workers each, 4 total on a 4-core
  box) while debugging the OpenMP issue: still contended. Had to pause one
  group entirely, let the other finish solo, then resume — simple sequential
  execution beat naive parallelism here given the actual bottleneck.
- First drafts of some module Markdown files (before this was clarified)
  leaned too close to paraphrased-but-still-long OCR transcription; the user
  explicitly corrected this mid-task: keep only techniques/methodology,
  condensed, no document rewrite.

## Payloads And Commands

```bash
# Full extraction pipeline for one CEH module (replace mNN and the PDF name)
S=/path/to/scratchpad
mkdir -p "$S/mNN"
pdftoppm -r 150 -gray -png "/home/kali/Downloads/CEH/CEHv13 - Module NN - <Name> hide01.ir.pdf" "$S/mNN/page"
ls "$S/mNN"/*.png | xargs -P 2 -I{} bash -c \
  'OMP_THREAD_LIMIT=1 tesseract "$1" "${1%.png}" -l eng; rm -f "$1"' _ {}
# then: concatenate $S/mNN/*.txt in page order, extract techniques only, write knowledge/ceh/mNN-*.md

# AFRICC link extraction (pptx is a zip)
unzip -o AFRICC_Deck.pptx -d /tmp/extract/deck
grep -roE 'https?://[^"<> ]+' /tmp/extract/deck/ppt/slides/ /tmp/extract/deck/ppt/slides/_rels/ | sort -u
```

## Flag / Outcome

- 21/21 CEHv13 modules + the AFRICC link index captured in `knowledge/ceh/`
  (M01-M20 + `africc-links.md`), all under ~10-22KB each (condensed, not raw
  dumps). No flag involved — outcome is the library itself plus the wiring
  into the active solving skills.
- One external-source pattern also captured from this prep round:
  `knowledge/patterns/misc/ldap-signing-bypass-ntlm-relay-specterops.md` (AD
  LDAP-signing bypass / NTLM relay, read from a SpecterOps blog post, rated
  low relevance for binary pwn, moderate for boot2root AD, most relevant as an
  attack-defense fallback).

## Reusable Lessons

- On this box, any OCR-heavy pipeline (not just CEH) must set
  `OMP_THREAD_LIMIT=1` (or `OMP_NUM_THREADS=1`) before every `tesseract` call
  when running more than one worker — otherwise apparent "hangs" are just
  OpenMP thread contention, and raising a watchdog's kill-threshold only
  masks the symptom instead of fixing it.
- Batch-render a whole PDF in one `pdftoppm` call, never page-by-page in a
  loop — the latter is the dominant source of slowness, not the OCR itself.
- Subagents running long background shell pipelines will report stale/
  optimistic status in their handback messages (background scripts keep
  running after the agent's turn ends); always verify real progress directly
  (`ls <dir>/*.txt | wc -l`, `ps aux | grep tesseract`) before trusting a
  "still waiting" or "done" claim.
- When asked to extract techniques from reference material, default to
  over-condensing and check in early rather than drafting a full page-by-page
  summary first — easy source for scope creep into "secretly re-authoring the
  whole document."
- Reuse existing escalation-router files (`*-triage/SKILL.md`,
  `category-switches.md`) as the integration point for new reference
  material — a knowledge file nobody's skill points to will not get read
  under time pressure mid-CTF.

## Pattern Candidates

- Existing pattern to update: none directly — this is reference material,
  not a single reusable exploit pattern.
- New pattern worth creating: `ocr-pipeline-openmp-thread-limit` under
  `knowledge/patterns/misc/` if another large scanned-PDF OCR job comes up —
  generalizes the `OMP_THREAD_LIMIT=1` + batch-render lesson above beyond this
  one CEH extraction.
