---
doc_kind: writeup
title: "External reference: SecBlog APT index + Adobe Reader PDF zero-day report"
category: misc
slug: secblog-apt-adobe-reader-zeroday-notes
created: 2026-10-22
status: reference
tags:
  - external-reference
  - apt
  - lazarus
  - pdf
  - adobe-reader
  - threat-intel
  - unverified
---
# External reference: SecBlog APT index + Adobe Reader PDF zero-day report

## Source

- Author: Mr_MaTriX (independent security blog "SecBlog")
- Page 1: https://salaheldinfikri.github.io/secblog/APT.html
- Page 2: https://salaheldinfikri.github.io/secblog/reports/adobe-reader-zerodday.html
- Nature: personal threat-intel/malware-analysis blog, not a CTF write-up, not an official vendor/CERT advisory.
- Reliability note (important): **no CVE is cited** for the Adobe Reader report, the author states code was reconstructed with AI assistance and "may not be the exact original code", and the methodology page itself is largely a navigation hub with the real technical content living in linked sub-pages that were not fetched. Treat everything below as an unverified third-party claim, useful as a methodology/IOC lead, not as confirmed ground truth.

## Page 1 — APT.html (index/hub)

- Site sections: Home, Reports, APTs, IOCs, YARA Rules, SIEM Reference, Structures, Achievements, About Me, CV.
- Stated 7-phase analysis methodology: threat intel gathering → sample collection + isolated lab → static analysis → dynamic analysis → reverse engineering → IOC extraction + MITRE ATT&CK mapping → detection engineering (YARA).
- Only one profile visible on the page itself: **Lazarus Group** (aliases: Hidden Cobra, Zinc). North Korean state-sponsored; tags APT/SUPPLY CHAIN/CRYPTO/ESPIONAGE, criticality CRITICAL. Associated malware names listed (no analysis on this page): AppleJeus, Destover, Volgmer, FALLCHILL, Dacls, Manuscrypt, Gopuram, VEILEDSIGNAL, ICONICSTEALER, AppleSeed.
- No TTPs, CVEs, IOCs (hash/domain/IP), commands, or code are present on this specific page — they live in linked sub-pages (Reports, per-APT pages, IOC feed, YARA feed) that were not retrieved.

## Page 2 — Adobe Reader PDF "zero-day" report

- Attributed initial discovery to Haifei Li (EXPMON).
- Claimed vuln class: abuse of Adobe Reader's JavaScript API (no memory corruption described) — presumed sandbox escape plus prototype pollution via `__defineGetter__`. The PDF/AcroForm is only the delivery/storage vector.
- Static triage tools cited: `pdfid.py`, `pdf-parser.py`, CyberChef, the `aesjs` JS library (AES-CTR) observed in the payload.
- `pdfid.py` findings reported: `/JavaScript` ×2, `/JS` ×1, `/AcroForm` ×1 (`/JS` in object 9, `/JavaScript` in objects 3 and 9, `/AcroForm` in object 1 pointing to object 2). JS obfuscated in JSFuck style (`+!+[]`-type expressions).
- Reported exploitation chain (see `knowledge/patterns/misc/malicious-pdf-js-obfuscation-c2-pattern.md` for the reusable technical pattern extracted from this):
  1. PDF open auto-triggers JS.
  2. Anti-sandbox delay via `app.setTimeOut(..., 500)`.
  3. Base64 payload read from AcroForm field `btn1` via `getField("btn1").value`.
  4. Multi-layer decode: Base64 → AES-CTR decrypt → zlib/deflate decompress.
  5. Large string lookup table hides indicators; index `557` reportedly resolves to the C2 address.
  6. System fingerprinting: OS (Win10), Reader version (≥21), platform (WIN), viewer type, 64-bit arch.
  7. HTTP-looking C2 beacon built from language/version/platform/open-docs + random nonce.
  8. Claimed privilege escalation via injection into `ANFancyAlertImpl` / `ANShareFile` reaching `SilentDocCenterLogin` with elevated rights, triggered by a forged button name.
  9. Covert C2 channel via `RSS.addFeed()` / `RSS.getFeeds()`, with a 500ms `setInterval` polling loop waiting on variables `bird0` (AES key) and `bird1` (ciphertext).
  10. Final execution via `eval(global.final_js)`, with a scheduled RSS feed cleanup at 2000ms.
- IOCs reported verbatim:
  - C2: `169.40.2.68:45191`
  - Referenced paths: `/c/windows/system32/ntdll.dll`, `/c/Windows/System32/bootsvc.dll`
  - Hex string marker: `ProductVersion`
  - Sample SHA256 (as extracted — length looked irregular in the summary, re-verify against the live page before using it as a real IOC): `65dca34b04416f9a113f09718cbe51e11fd58e7287b7863e37f393ed4d25dde7`
  - MITRE ATT&CK techniques listed: T1566.001, T1059.007, T1204.002, T1027, T1140, T1082, T1071.001, T1105, T1571.
  - Noted on 2026-04-07: C2 server responded without delivering a payload — suggested victim filtering by the attacker.

## Why this is logged

- Not a solved CTF challenge; no flag. Logged because it documents a reusable forensics/malware-analysis methodology (PDF with `/JS` + `/AcroForm`, JSFuck unpacking, AcroForm-stashed payload, layered decode, RSS-as-covert-channel) that could map directly onto a rev/forensics CTF challenge using the same tricks. See the extracted pattern file for the actionable version.

## Follow-ups not yet done

- Sub-pages of the APT.html hub (Reports, per-APT detail pages, IOC feed, YARA feed) were not fetched — they likely contain the real IOC/YARA/ATT&CK detail behind the index page and may be worth pulling if Lazarus Group or related malware families become relevant to a task.
- The irregular-looking SHA256 above should be re-checked against the live page rather than trusted as-is.

## Related Patterns

- `knowledge/patterns/misc/malicious-pdf-js-obfuscation-c2-pattern.md`
