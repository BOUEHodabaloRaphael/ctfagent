---
doc_kind: writeup
title: "battleCTF Qualifier (bugpwn) — VULN#005 Acme Gateway / GoAhead 6.1.1 (solved on platform; no confirmed bug found in this session's recorded recon)"
category: misc
slug: bugpwn-vuln005-goahead-recon-gap
created: 2026-11-10
status: solved
tags:
  - vuln-research
  - goahead
  - embedded-web-server
  - gap-in-notes
source: "ctf.bugpwn.com — battleCTF Qualifier 2026 (challenge id 25, Vuln Research, 30 pts)"
target: "169.58.126.107:7020 — \"Acme Gateway\" IoT device management portal, nginx reverse proxy in front of GoAhead 6.1.1"
---
# battleCTF Qualifier — VULN#005

## Challenge Summary

- An IoT device-management portal ("Acme Gateway") running **GoAhead v6.1.1** behind an nginx
  reverse proxy, self-reporting an internal address `192.168.0.3:8080`. Confirmed via
  `git diff v6.1.1 HEAD -- src/` against upstream `embedthis/goahead` that this is the **latest**
  version — zero commits after it touch `src/` — so the bug here is **not** a known published CVE
  and had to be found by source review/fuzzing. Confirmed `solved_by_me: true` on the platform,
  but **this workspace's own recorded session never found a working bug** — the notes end at
  "Status: Not yet solved" with an extensive, honestly negative recon trail. This writeup documents
  that recon (genuinely useful if this target is revisited) and states the gap plainly rather than
  inventing a resolution.

## Attack Surface Mapped

- `/` → 302 to `/index.html` (static content; flavor text mentions "svc process pool",
  "acme-gw-44xx", "90 day log purge").
- `/admin/` and `/admin/index.html` → 401 Basic auth, realm `example.com`.
- All other guessed paths (`/cgi-bin/`, `/goform/`, `/upload`, `/api/`, `/action/*`, `/jst/`,
  `/private/`, `/auth/*`, `/tmp/`) → 404.
- Rate limiting kicks in after ~3-5 requests with unusual methods or failed auth — brute force
  explicitly ruled out as the intended path.
- `POST multipart/form-data` to `/` or `/index.html` reliably triggers a `500 Internal Server
  Error`, but the service stays fully stable afterward (confirmed via follow-up GETs) — a handled
  error path (likely a sandboxed `/tmp` write failure), not memory corruption. Ruled out.

## Vulnerability Classes Checked and Ruled Out (via source read + live verification)

- **Basic-auth timing attack (CVE-2021-43298 class)**: `pmatch()` in `auth.c` (~line 631) is
  constant-time (compares full max-length, folds the length difference into the result) — patched.
- **CGI env-var injection / LD_PRELOAD (CVE-2017-17562 class)**: `cgi.c` blacklists `LD_`, `LDR_`,
  `_RLD`, `DYLD_` prefixes and the Shellshock `=()` pattern before building `envp`; `/cgi-bin` is
  also not even reachable on this deployment (404 either way).
- **Path traversal in `websNormalizeUriPath`**: reviewed in full (`http.c` ~line 2795); segment-
  based `..`/`.` handling is bounds-checked, clamps at root, no negative-index UB found on manual
  trace.
- **Upload filename path traversal**: `processUploadHeader` rejects filenames starting with `.` or
  containing shell/path metacharacters; the real stored temp path is server-generated via
  `websTempFile()` — the client-supplied filename is cosmetic only, not usable as a real path.
- **Host-header reflection in the redirect `Location:` header**: confirmed the Host header *is*
  reflected unsanitized in the proxied response's `Location:` header for `GET /`, but traced this
  to nginx's own default `proxy_redirect` host-rewriting behavior, not a GoAhead bug — the static
  HTML body (with the hardcoded internal address) comes from GoAhead's `websRedirect()` using a
  static config value, confirmed via source read, not the request's Host header. Out of scope
  (nginx isn't part of the provided source).
- **Format-string / unchecked `strcpy`/`sprintf` audit**: grepped every instance across `src/*.c` —
  all use fixed known-safe strings or correctly pre-sized buffers.
- **`/action` handler**: uses a bounded `scopy(actionBuf, sizeof(actionBuf), wp->path)` and cleanly
  404s for undefined actions; may not even be enabled on this deployment.
- **Default/sample credentials**: `src/auth.txt`/`test/auth.txt` ship a demo Blowfish-salted
  `admin` hash with every GoAhead release — tried a handful of common guesses (not the salted
  default, which isn't crackable from the hash alone) before the rate limit made further brute
  force both impractical and against fair-play norms. Not pursued further.

## Not Yet Reviewed When Notes Stop (the real next steps)

- **`js.c`/`jst.c`** (2267 + 260 lines) — GoAhead's custom embedded JS/template interpreter, a
  classic source of real memory-corruption bugs in embedded web servers. `/jst/` 404s externally,
  but the interpreter might still be reachable via a registered `.asp` extension or a catch-all
  route if any `.jst`/`.asp` file exists in the real doc root (only `/index.html`'s existence was
  confirmed, the full doc root was never enumerated).
- **`runtime.c`** (2726 lines, symbol table/variable storage) — not audited.
- **`socket.c`** (1399 lines, raw socket/buffer handling) — not audited.
- Open hypothesis: the flag might not be behind RCE/auth-bypass at all, but behind triggering a
  *specific* crash with a specific payload shape — the one confirmed 500 might be the right bug
  family, just not yet the right exact payload (e.g. malformed/duplicate `Content-Disposition`
  headers, in the shape of the CVE-2019-5096 UAF pattern).

## Gap — Explicit, Not Guessed

**No working bug or flag-producing payload is recorded in this workspace.** The notes end with
"0/2 submission attempts used so far (flag not yet found, nothing submitted)." The platform
confirms `solved_by_me: true`, but **the submissions log for this CTF contains no entry for this
challenge's id (25) at all** — meaning the actual solve happened entirely outside this session's
tracked tooling, with zero trace of the final technique anywhere in this repo. If `js.c`/`jst.c`
was the answer, it was never confirmed here.

## Flag / Outcome

- Not recorded in this repo. `solved_by_me: true` is the only confirmation available.

## Reusable Lessons

- `git diff v<version> HEAD -- src/` against the upstream of a provided library/server source is a
  fast, decisive way to confirm "this is the latest version, the bug is undisclosed" before
  investing in CVE-matching — redirects effort toward source review/fuzzing immediately instead of
  searching for a public writeup that doesn't exist.
- An embedded web server's own custom scripting/template interpreter (here, GoAhead's `js.c`/
  `jst.c`) is consistently a higher-value audit target than the well-trodden HTTP/auth/CGI code
  paths, precisely because it's less publicly scrutinized — worth prioritizing earlier in a
  source-review pass on this kind of target rather than last.
- When a workspace's notes end mid-investigation with real negative results but the platform shows
  it solved anyway, write that discrepancy down explicitly (as here) rather than letting the gap
  disappear silently — it tells a future session exactly how much of the recorded recon can be
  trusted as "still true" versus genuinely unknown.

## Related

- [`bugpwn-vuln003-cares-cve-2020-8277`](bugpwn-vuln003-cares-cve-2020-8277.md) — the other
  "Vuln Research" challenge on this platform, where the bug itself (though not the exact trigger)
  was fully confirmed via source diff, a sharper contrast to this challenge's larger gap.
