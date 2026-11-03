---
doc_kind: pattern
title: "OCR pipeline: batch-render + OMP_THREAD_LIMIT=1 (avoid false hangs)"
category: misc
slug: ocr-pipeline-openmp-thread-limit
created: 2026-11-03
status: active
tags:
  - ocr
  - tesseract
  - pdftoppm
  - openmp
  - performance
  - tooling
chain_summary: "Large scanned-PDF OCR jobs look hung/pathological-page-stuck when tesseract oversubscribes OpenMP threads across parallel workers; fix is OMP_THREAD_LIMIT=1 per call plus whole-PDF batch rendering, not a watchdog kill-threshold bump."
---
# OCR pipeline: batch-render + OMP_THREAD_LIMIT=1 (avoid false hangs)

## Chain Summary

- One-line chain: Large scanned-PDF OCR jobs look hung/pathological-page-stuck when tesseract oversubscribes OpenMP threads across parallel workers; fix is OMP_THREAD_LIMIT=1 per call plus whole-PDF batch rendering, not a watchdog kill-threshold bump.
- Typical target shape: any scanned/image-only PDF corpus (no extractable text via `pdftotext`) that needs bulk OCR with more than one parallel worker on a shared-core box.

## Preconditions

- `pdftotext` on the source PDF yields nothing useful (watermark noise, empty, or garbage) — confirms it's image-only and OCR is required.
- More than one `tesseract` process will run concurrently (e.g. `xargs -P 2` or several background pipelines at once) on a machine with few cores (here: 4).

## Cheap Probes

- Render and OCR a single sample page first: `pdftoppm -r 150 -gray -png file.pdf test-page -f 1 -l 1 && time tesseract test-page-1.png out -l eng`. Note the wall time.
- If a page "hangs" past the expected time under parallel load, re-run the exact same page alone with `OMP_THREAD_LIMIT=1 tesseract page.png out -l eng` and compare timing — a dramatic drop (minutes → seconds) confirms OpenMP thread contention rather than a genuinely pathological page.

## Telltale Evidence

- `ps -o pid,etimes,cmd -p <pid>` shows a `tesseract` process with `etimes` far beyond the normal per-page time (normal here: 90-110s at 150dpi, dense pages up to ~259s) — and this happens consistently on *multiple concurrent* processes at once, not on isolated single runs.
- Raising a watchdog's kill-threshold (90s → 240s → 320s) does not fix throughput, it just moves the symptom — a strong sign the real bottleneck is resource contention (CPU/threads), not per-page content.
- CPU core count is at or near 100% busy with only 2-4 `tesseract` processes running — each one is trying to grab `nproc` OpenMP threads for itself.

## Escalation Order

1. Batch-render the whole PDF in one `pdftoppm -r 150 -gray -png file.pdf out/page` call — never loop page-by-page with separate `pdftoppm` invocations per page, that alone can be the dominant slowdown (~1 page/2min observed) independent of OCR.
2. OCR the PNGs with `OMP_THREAD_LIMIT=1` (or `OMP_NUM_THREADS=1`) set on every `tesseract` invocation, parallelized via `xargs -P N` where N ≈ core count (not more), deleting each PNG right after its OCR to bound disk usage:
   `ls out/*.png | xargs -P 4 -I{} bash -c 'OMP_THREAD_LIMIT=1 tesseract "$1" "${1%.png}" -l eng; rm -f "$1"' _ {}`
3. If multiple independent OCR jobs/agents must share the same box, treat total worker count (sum across all jobs) as the real parallelism budget, not per-job — e.g. 2 jobs × 2 workers each already uses all 4 cores; adding a 3rd job's workers will contend even with the thread-limit fix applied.
4. Only add a watchdog (kill stuck `tesseract` past some generous timeout) as a safety net for truly pathological pages (rare, dense diagrams) *after* the thread-limit fix is in place — not as the primary fix.

## Common Mistakes

- Treating a "stuck" OCR process as a pathological/corrupt page and tuning a kill-threshold upward repeatedly, when the actual cause is thread oversubscription that no threshold adjustment resolves.
- Running 2+ independent parallel pipelines (each spawning its own `-P 2` or more) on a shared low-core-count box without coordinating total concurrency — looks like "just add more agents" but actively slows every pipeline down.
- Letting a kill-on-timeout wrapper also delete the source PNG (`rm -f "$1"` unconditional on timeout), which forces a full re-render from the PDF for that page — fine if rare, costly if the kill-threshold was wrong and many normal pages get killed.

## Payload Shapes

```bash
# Full-PDF render (fast, one process) then thread-limited parallel OCR
pdftoppm -r 150 -gray -png "/path/to/scanned.pdf" "$SCRATCH/out/page"
ls "$SCRATCH/out"/*.png | xargs -P "$(nproc)" -I{} bash -c \
  'OMP_THREAD_LIMIT=1 tesseract "$1" "${1%.png}" -l eng; rm -f "$1"' _ {}
```

## Related Writeups

- [CEHv13 + AFRICC reference library](../../writeups/misc/ceh-africc-reference-library.md) — the job where this was discovered, extracting 21 CEHv13 modules (~3800 pages) via this exact pipeline.

## Skill Impact

- Related skill: none of the current triage skills run OCR directly; this is a general tooling lesson for any future bulk-document-extraction task (e.g. another CTF prep, a forensics challenge with scanned evidence).
- Rule to add or update: if a future skill or helper script does bulk OCR, default to `OMP_THREAD_LIMIT=1` and whole-document batch rendering from the start rather than rediscovering this.
