---
doc_kind: pattern
title: "Malicious PDF: AcroForm-stashed JSFuck payload with layered decode and covert RSS C2"
category: misc
slug: malicious-pdf-js-obfuscation-c2-pattern
created: 2026-10-22
status: draft
tags:
  - pdf
  - javascript
  - jsfuck
  - obfuscation
  - c2
  - malware-analysis
  - acroform
---
# Malicious PDF: AcroForm-stashed JSFuck payload with layered decode and covert RSS C2

## Chain Summary

- One-line chain: a PDF's embedded JavaScript is JSFuck-obfuscated, stores its real payload Base64-encoded inside an AcroForm field value (not in the JS object itself), then decodes/decrypts/decompresses it in memory and uses a non-network-looking API (RSS feed functions) as a covert C2 channel before a final `eval`.
- Typical target shape: a forensics/rev CTF challenge or malware sample that hands you a `.pdf` with `/JavaScript` and `/AcroForm` objects and expects static string search alone to come up empty.

## Preconditions

- PDF viewer JS engine executes embedded `/JS` / `/JavaScript` on open (Adobe Reader-style `app`/`getField`/`RSS` APIs, or an emulator that implements them).
- Challenge/sample stores its real payload as data in a form field (`getField("btn1").value` in the observed case) rather than as a JS literal, so naive de-obfuscation of the JS object alone won't reveal it.

## Cheap Probes

- `pdfid.py sample.pdf` — quick triage: counts of `/JavaScript`, `/JS`, `/AcroForm`, `/OpenAction`, `/Encrypt`.
- `pdf-parser.py -o <objnum> sample.pdf` on each object flagged by pdfid to pull raw JS source per object.
- Grep the extracted JS for JSFuck's signature character classes: only `[]()!+` present, e.g. `+!+[]` — if found, the real logic is hidden and needs re-execution/deobfuscation (sandboxed `eval` in a disposable JS runtime, or an online JSFuck decoder), not manual reading.
- Grep decoded JS for `getField(` calls — the string argument is the AcroForm field name holding the actual payload, separate from the JS object.
- Grep for `RSS.addFeed`, `RSS.getFeeds`, `app.setTimeOut`, `__defineGetter__` — these indicate covert-channel / anti-sandbox / prototype-pollution tricks rather than ordinary script logic.

## Telltale Evidence

- `pdfid.py` shows `/JS` and `/JavaScript` in different object numbers than `/AcroForm` — the AcroForm object is the data container, the JS object is only the loader.
- Decoded JS body is almost unreadable at first glance but, once JSFuck is unpacked, resolves to ordinary function calls with Base64/hex string literals.
- A `setInterval`/polling loop waiting on two externally-settable variable names (observed as `bird0`/`bird1` — an AES key and ciphertext) before calling `eval` on a globally-stashed function body (observed as `global.final_js`) is the hand-off point from "decode" to "execute".
- A delay via `app.setTimeOut(..., 500)` right after document open is a classic anti-sandbox timing trick (automated analysis sandboxes often don't wait for timers).

## Escalation Order

1. Static triage: `pdfid.py` then `pdf-parser.py` per flagged object to get raw JS and confirm AcroForm field names referenced by the JS.
2. If the JS is JSFuck (only `[]()!+` characters), deobfuscate by executing it in an isolated/disposable JS sandbox (never in the real target app) and dumping the resulting source instead of trying to read JSFuck by eye.
3. Follow every `getField("<name>").value` reference back to the corresponding AcroForm field's value in the PDF object stream — that's where the real payload (often Base64) lives, not in the JS object.
4. Decode layer by layer in the order the script applies them (commonly Base64 → symmetric decrypt, e.g. AES-CTR with a key supplied via a separate channel/variable → zlib/deflate decompress). Use CyberChef or a short Python/Node script to replicate each step offline.
5. Look for a large string/lookup table used to de-reference indices to real strings (IPs, DLL paths, etc.) — treat a literal numeric index into that table as the path to the actual IOC rather than a meaningless magic number.
6. Identify the final `eval` target variable (e.g. a global the decoder assigns to) — that's the actual payload logic; everything before it is just the delivery/anti-analysis wrapper.
7. Note any fingerprinting calls (OS/version/viewer/arch) feeding into an HTTP-looking beacon URL — useful both as IOCs and as a hint that the sample/challenge gates its "real" payload behind an environment check (may need to spoof those values in a sandboxed re-run to reach later behavior).

## Common Mistakes

- Trying to read JSFuck by eye instead of just executing it in a sandbox and capturing the deobfuscated output.
- Searching only the `/JS` object for the "real" payload and missing that it's stashed in an unrelated AcroForm field value.
- Assuming `RSS.addFeed()` / `RSS.getFeeds()` are benign/unused viewer features — in this pattern they're repurposed as a non-HTTP-looking read/write channel for key + ciphertext exchange.
- Treating a reconstructed/AI-assisted deobfuscation as ground truth without caveats — if the source material itself says the exact original code isn't guaranteed, keep IOC/technique claims as "reported", not confirmed, until independently verified.
- Forgetting the anti-sandbox delay (`setTimeOut`) — static extraction of strings may miss behavior that only fires after the delay in a real/dynamic run.

## Payload Shapes

```text
# static triage
pdfid.py sample.pdf
pdf-parser.py -o <N> sample.pdf        # dump raw object N (the /JS or /AcroForm object)

# JSFuck signature to grep for in extracted JS
+!+[]

# typical call chain to trace by hand after deobfuscation
app.setTimeOut(fn, 500)                 # anti-sandbox delay
getField("btn1").value                  # payload stash, NOT in the JS object
# Base64 decode -> AES-CTR decrypt (key from a separate var, e.g. bird0) -> zlib inflate
stringTable[557]                        # index into a lookup table -> real IOC (e.g. a C2 address)
RSS.addFeed(...) / RSS.getFeeds(...)     # covert channel carrying bird0 (key) / bird1 (ciphertext)
eval(global.final_js)                   # final execution hand-off
```

## Related Writeups

- `knowledge/writeups/misc/secblog-apt-adobe-reader-zeroday-notes.md` (external reference notes; unverified third-party report, no CVE, author-acknowledged AI-assisted reconstruction — treat as a methodology lead, not a confirmed technical source)

## Skill Impact

- Related skill: `rev-triage` (static/dynamic RE triage) could add a "PDF with /JS + /AcroForm" branch pointing at this pattern.
- Rule to add or update: in `rev-triage`, when a PDF sample shows `/JavaScript` or `/JS` via `pdfid.py`, check for JSFuck-style obfuscation before manual reading, and always cross-reference `getField()` names against AcroForm field values rather than assuming the payload is inline in the script object.
