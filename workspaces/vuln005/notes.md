# VULN#005 — Solve Notes (in progress)

## Target
`169.58.126.107:7020` — "Acme Gateway" IoT device management portal.
Behind nginx reverse proxy -> internal GoAhead instance (self-reported internal addr `192.168.0.3:8080`).
Source: GoAhead **v6.1.1** — confirmed via `git diff v6.1.1 HEAD -- src/` against upstream `embedthis/goahead`
that this is the LATEST version (zero commits after it touch src/). So the bug is NOT a published CVE —
must be found via source review / fuzzing.

## Attack surface discovered (live probing)
- `/` -> 302 to `/index.html` (200, static content, flavor text about "svc process pool", "acme-gw-44xx", "90 day log purge")
- `/admin/` and `/admin/index.html` -> 401 Basic auth required, realm="example.com"
- All other guessed paths (`/cgi-bin/`, `/goform/`, `/upload`, `/api/`, `/action/*`, `/jst/`, `/private/`, `/auth/*`, `/tmp/`) -> 404
- Rate limiting active after ~3-5 requests with unusual methods or failed auth attempts (429) — brute force not viable/intended path
- POST multipart/form-data to `/` or `/index.html` -> reliably 500 Internal Server Error, BUT service stays fully stable/responsive afterward (confirmed via follow-up GETs) -> NOT a crash/memory corruption, just a handled error path (likely /tmp write failure in sandboxed deployment, or similar benign condition). Ruled out as the vuln.

## Things ruled out (verified in source, v6.1.1 already patched/safe)
- **Basic auth timing attack (CVE-2021-43298 class)**: `pmatch()` in auth.c (line ~631) is constant-time, compares full max-length, includes length-diff in result. Patched.
- **CGI env var injection / LD_PRELOAD (CVE-2017-17562 class)**: `cgi.c` blacklists `LD_`, `LDR_`, `_RLD`, `DYLD_` prefixes and `=()` (shellshock pattern) before building envp. Also `/cgi-bin` not even reachable on this deployment (404).
- **Path traversal in websNormalizeUriPath**: reviewed in full (http.c ~2795). Segment-based `..`/`.` handling looks correct and bounds-checked (clamps at root, no negative index UB found on manual trace).
- **Upload filename path traversal**: `processUploadHeader` rejects filenames starting with `.` or containing `\/:*?<>|~"'%\`^\n\r\t\f`; also the actual stored temp path is server-generated via `websTempFile()`, client filename is cosmetic only (not used as real path). Not exploitable for arbitrary write.
- **Host header reflected in `Location:` redirect header**: confirmed Host header IS reflected unsanitized in the `Location:` response header for `GET /` (302). BUT traced to nginx's default `proxy_redirect` behavior (rewrites backend's Location host:port to match client Host when it matches the upstream target) — NOT a GoAhead application bug. The static HTML body (with hardcoded `192.168.0.3:8080` internal address) comes from GoAhead's own `websRedirect()` which uses a static `websHostUrl` config value, not the request Host header — confirmed via source read of `http.c:websRedirect()`. Ruled out as in-scope (nginx isn't part of the provided source).
- **Format string / strcpy audit**: grepped all `strcpy`/`sprintf`/format-arg patterns across `src/*.c`. All found instances use fixed known-safe strings or pre-sized buffers (e.g. `websMD5Block` allocation is exactly sized for prefix+hash). No obvious overflow found by inspection.
- **`/action` handler**: `actionHandler` in action.c uses `scopy(actionBuf, sizeof(actionBuf), wp->path)` (bounded) and cleanly 404s for undefined actions. Route may not even be enabled on this deployment (indistinguishable 404 either way).

## Default/sample credentials found in source (src/auth.txt, test/auth.txt)
- `admin:BF1:00128:ILrUswPoHBSweW5R:UW5fySh5ZQ0pUvlwOFBbbz43UElaQeyw` (salted Blowfish, from `src/auth.txt` — ships with every GoAhead release as demo default, NOT likely the live deployment's real credential)
- Tried a handful of common guesses (admin:admin, admin:password, joshua:joshua, etc.) — all 401 or rate-limited (429) before getting far. Brute force is actively mitigated (429 after ~3-5 attempts) — NOT the intended path, stopped to avoid hammering the shared instance.

## Next angles to investigate (not yet done)
- **`js.c` / `jst.c`**: custom embedded JS/template interpreter (2267 + 260 lines). Classic source of real memory-corruption bugs in embedded web servers. Not yet reviewed in depth. `/jst/` route 404s externally but the interpreter might be reachable via a different registered extension (`.asp`) or via `/` catch-all if any `.jst`/`.asp` file exists in the actual doc root (unknown — we only confirmed `/index.html` exists).
- **`runtime.c`** (2726 lines) — symbol table / variable storage, not yet audited.
- **`socket.c`** (1399 lines) — raw socket/buffer handling, not yet audited.
- Consider: maybe the "flag" isn't behind RCE/auth-bypass at all but behind successfully triggering a specific crash with a *specific* payload shape (the single 500 we got might be the right family of bug, just not yet the right payload — e.g. malformed/duplicate Content-Disposition headers, as discussed re: CVE-2019-5096 UAF pattern, worth a few more careful crafted multipart payloads with attention to NOT spamming the shared instance).

## Status
Not yet solved. Extensive recon done, several plausible bug classes ruled out via source reading + live verification.
0/2 submission attempts used so far (flag not yet found, nothing submitted).
