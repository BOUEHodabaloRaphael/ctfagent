# OT#003 — Progress Notes

## Target
- 169.58.126.107:6002 — "Rhein-Vogt Steelworks" Plant Operations Portal (Express/Node behind openresty)

## Confirmed exploit chain
1. `/commissioning-notes.txt` leaks creds: `operator` / `St33lW0rks!2024`
2. Login → `/dashboard` shows a **static/hardcoded** "nominal" status (620°C) that never changes regardless of real state — pure UI, not read from any backend.
3. Dashboard has an SSRF primitive: `POST /ops/test-sensor` with form field `url=` (or JSON body `{"url":...}`), backend does `fetch(url)` server-side.
4. SSRF filter blocks literal `localhost`, `127.0.0.1`, dotted private IPs (10/8, 172.16/12, 192.168/16), and any URL containing the substring `furnace` (checked anywhere in the full URL string, case-sensitive).
   - **Bypass**: decimal (or octal) integer IP form, e.g. `172.25.0.2` → `http://2887319554:PORT/...` — filter only regexes the dotted form, fetch() still resolves/connects fine.
   - Hostnames that DNS-resolve to internal IPs without the blocked keywords also bypass it (found `gateway` → 172.25.0.3).
5. Internal docker network: `172.25.0.0/24`. Only `.1` (gateway, nothing listening), `.2` (**furnace control app, port 4000**), `.3`/`.4` (both appear to be the portal app itself, maybe network aliases) respond. All other addresses in that /24 give `EHOSTUNREACH` (no ARP entry — confirms only 4 hosts exist).
6. **Method-override discovery (important)**: sending the request to `/ops/test-sensor` as JSON (`Content-Type: application/json`) with `{"url":...,"method":"POST"}` makes the backend actually issue that HTTP method against the target (confirmed via "Cannot POST /x" vs "Cannot GET /x" responses differing) — turns the GET-only SSRF oracle into an arbitrary-method SSRF.
   - `body` field (as a JSON-encoded *string*, not object) is also forwarded, but furnace control doesn't seem to read/need it for `/vent`.
   - `headers` field was tried (Authorization/X-Api-Key/X-Internal) — accepted without erroring but no observed behavior difference.
   - **`OPTIONS` and sometimes other odd methods intermittently crash the portal's Node backend** (502 Bad Gateway for roughly 30–90s, then auto-recovers via what's presumably a process supervisor). Happened twice independently (once clearly after an OPTIONS call, once on an ordinary POST to `/safe_mode` with no OPTIONS involved — so it may be a bit flaky/random, not purely OPTIONS-triggered). **Avoid hammering; space requests out.**

## Furnace control (172.25.0.2:4000) surface — fully enumerated
- `GET /status` → `{"temperature":1550,"pressure":92,"vented":false,"ruptured":false}` (live telemetry; genuinely different from the portal dashboard's fake "620°C nominal" — the core vuln story: portal operators are blind to the real state).
- `POST /vent` → `{"ok":true,"pressure":35,"vented":true}` — a real, persistent write action (confirmed via subsequent `/status` reflecting the change). Idempotent/fixed output regardless of body content. **State resets to baseline (92/false) after some idle period or backend restart** — not time-bomb/incremental building that we observed.
- Everything else (~230 distinct GET words, ~70 distinct POST words — generic API wordlist + OT/ICS/blast-furnace specific jargon: vent synonyms, valve/relief/scram/rupture/burst/overpressure/meltdown, admin/debug/secret/flag/key/token endpoints, ticket refs, SSO paths, SQLi in login, nested `/unit/2/...` style paths, etc.) → 404 "Cannot GET/POST X" (genuinely doesn't exist, confirmed via Express's default handler).
- Only ports open internally: `.2:4000` (furnace control), `.3:3000`/`.4:80` (portal itself). No Modbus/S7/DNP3/OPC-UA/MQTT/BACnet ports open anywhere in the /24.
- Query-param fuzzing on `/status` (key/token/auth/secret/pass/password/api_key/etc.) — no effect, always returns the same baseline reading.
- `file://`, `gopher://`, `dict://` schemes rejected by node-fetch ("Only HTTP(S) protocols supported").

## Rate limiting / session behavior (useful for future probing)
- `/ops/test-sensor` rate-limits per request-burst: roughly ~20 requests succeed, then "rate limited, try again later" for a good while. A **genuine ~600s idle wait reliably clears it** (confirmed multiple times); shorter backoffs (30s, 150s) did NOT reliably clear it.
- The session cookie (`sid`) has a **short TTL** — expires mid-run even during slow, spaced-out probing, giving a portal-level 302 "Found. Redirecting to /login" from `/ops/test-sensor` (NOT a furnace-control response!). **Any script must detect this specific string and re-login**, otherwise every subsequent "result" is a false positive (this bit us once — got 3 false "HIT"s before realizing `plant`/`mill`/`facility` were actually session-expiry redirects, not real furnace routes).

## Open questions / not yet found
- No flag string found anywhere (response bodies, headers, dashboard HTML, error pages).
- No destructive/dangerous write action found beyond the safe `/vent`. No `/rupture`, `/burst`, `/scram`, etc.
- No externally-hosted briefing page exists for OT#003 on otctf.pages.dev (unlike OT#001/OT#002, which do — see workspaces/ot-002/challenge.md for that pattern). This challenge's full spec is only the short blurb given in chat.

## Ideas not yet tried
- PATCH/other unusual methods on `/status` or `/vent` (avoided after the 502 crashes — be careful, space out, maybe only try once after confirming service healthy).
- JSON field name variations beyond `body`: `data`, `payload`, `content`.
- Checking whether repeated `/vent` calls over a longer real-time window (hours) ever change behavior (we only sustained ~2.5 hours).
- Reconsidering that the flag might not be string-embedded at all — e.g. awarded by the CTF platform itself once a specific detectable condition is met server-side, not retrievable via more HTTP probing from here.

## STATUS CHECK (2026-10-25 15:11 UTC)
- Platform metadata (id=30): value=136, solves=8, solved_by_me=False, attempts=0, state=visible.
  connection_info `169.58.126.107 6002` unchanged, `files=[]` unchanged (no attachment).
  No description/connection_info change detected since last recorded.
- Note: the main agent is currently focused exclusively on OT#004 (id=33), so this is a passive
  status check only — no new probing done here.
- Most promising next concrete step: try PATCH (and other non-GET/POST methods) against
  `/ops/test-sensor`'s target `/vent` and `/status` routes on the furnace control service, since
  that's the one concrete untried idea in the existing notes — but space it out carefully given
  the known 502 flakiness, and only after confirming the portal is currently healthy.

## RE-PROBE (2026-10-25 15:32-15:34 UTC) — method-override methods + body field-name variants

Session TTL confirmed short but re-login worked cleanly once at script start; no mid-run
expiry hit this time (19 `/ops/test-sensor` calls total, ~5s apart, stayed under the ~20-burst
rate limit; no 502s, no crashes).

**Baseline before testing**: `GET /status` → `{"temperature":1550,"pressure":92,"vented":false,"ruptured":false}` — unchanged from prior session, confirms no idle-reset happened between runs.

**Unusual methods via method-override SSRF (`{"url":...,"method":M}`), tried PATCH/PUT/DELETE/HEAD/TRACE against both `/status` and `/vent`:**
- PATCH, PUT, DELETE, TRACE on both paths → furnace-control's own Express default 404 handler,
  verbatim `Cannot <METHOD> /status` / `Cannot <METHOD> /vent` (confirms furnace-control itself,
  not Express generically, has no route registered for any of these methods on either path —
  i.e. only GET/POST are wired up at all, not just on `/status`/`/vent` but implicitly across the
  whole app, consistent with the ~230/~70-word full enumeration already done).
- HEAD `/status` → `200 {"status":200,"body":""}` — expected Express HEAD-mirrors-GET-headers
  behavior, empty body (HEAD never returns a body), not a new route.
- HEAD `/vent` → `404 Cannot HEAD /vent` — expected, since `/vent` is POST-only; HEAD doesn't
  match a POST route.
- **No crashes/502s from any of PATCH/PUT/DELETE/HEAD/TRACE this round.** OPTIONS was *not*
  retried this session (per instructions, avoided given documented crash risk; nothing else
  found that would justify the risk).
- Conclusion: method-override does NOT unlock any hidden handler on `/status` or `/vent`. This
  idea is now exhausted — only GET/POST exist on the furnace-control app, full stop.

**Body field-name variants (`data`, `payload`, `content` as extra top-level JSON fields alongside `url`/`method` in the SSRF request to `/ops/test-sensor`, mirroring the already-tried `body` field):**
- `POST /vent` with `+data` / `+payload` / `+content` → all three returned the same fixed
  `{"ok":true,"pressure":35,"vented":true}` — identical to calling `/vent` with no extra field at
  all. No behavior difference based on field name.
- `GET /status` with `+data` / `+payload` / `+content` → all three returned the live telemetry
  reflecting the vent calls above (`pressure:35, vented:true`), again identical to calling
  `/status` plain. No field-name-dependent behavior.
- Conclusion: furnace-control's `/vent` and `/status` handlers simply ignore the request body
  entirely regardless of which top-level field carries it (`body`/`data`/`payload`/`content`).
  This idea is now exhausted too.

**Furnace state after this session**: vented (pressure 35, vented:true) — a direct, intended,
non-destructive side effect of the `/vent` calls used to test field names. State is known to
reset to baseline (92/false) after an idle period per earlier notes, so this is not a lasting
change.

**No flag found** in any response body, header, or error page across all of the above.

**Updated open-question status**: both of the two concrete "ideas not yet tried" from the prior
entry (unusual methods; body field-name variants) have now been tried and are negative. The
furnace-control app's surface is confirmed fully closed: GET `/status`, POST `/vent`, nothing
else, no other method, no other body-field dependency. Remaining avenues from the "open
questions" section (long-duration `/vent` behavior over hours; the possibility the flag is
awarded by a platform-side detectable condition rather than embedded in any response) are now
the most plausible remaining leads — HTTP-probing this specific furnace-control/method-override
angle appears to be a dead end.
