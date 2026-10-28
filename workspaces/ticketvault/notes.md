# TicketVault (web, 100 pts) — in progress

Target: 144.217.91.111:3001 (Node/Express + MongoDB, source: server.js + package.json given)
Scenario: IDOR-style — every user has own tickets; admin's inbox holds post-mortem we shouldn't read.

## Source review (server.js)
- Two custom utils NOT provided: `./utils/sanitize.js` (resolveLoginCredentials, used ONLY on
  /login, not /register) and `./utils/ticketFilter.js` (buildScopedFilter, used on /tickets/search).
  Both withheld deliberately — vuln is inside one of them.
- /register: raw `db.collection('users').findOne({ username })` + insertOne, NO type validation.
- /login: goes through resolveLoginCredentials(req) before the findOne — looks hardened.
- /tickets/search has a UI-advertised "Advanced filter (JSON, power users)" `filter` query param,
  the obvious bait for NoSQL injection.

## What's ruled out (tested live against the real instance)
- Register "admin": blocked, "Username already taken" → real admin account exists.
- Login NoSQL injection via JSON body (`password: {"$ne": null}}`, `{"$gt": ""}`): both fail,
  returns the normal invalid-credentials page. resolveLoginCredentials appears to genuinely
  sanitize (likely coerces to string).
- Regex-based login bypass (`password: ".*"` as plain string, hoping server wraps it in $regex):
  fails too.
- `/tickets/search?filter=...` owner-key manipulation: tried `{"owner":"admin"}`,
  `{"owner":{"$ne":"testuser123"}}`, `{"owner":{"$regex":"^a"}}`, `{}` (empty), `{"$where":"true"}`
  — ALL consistently return only our own ticket. `owner` genuinely cannot be influenced from the
  `filter` param (likely $and-wrapped server-side, or a field whitelist). `subject`/`content` DO
  get applied (narrowing works, confirmed with a matching vs non-matching subject test) — so the
  parameter is live and parsed, just not exploitable via `owner` override.
- Static source leakage: /server.js, /db.js, /utils/sanitize.js, /utils/ticketFilter.js,
  /package.json, /.env — all 404, no express.static misconfig.
- Theoretical session-corruption via malicious `username` object at /register (e.g.
  `{"$exists":false}`) DOES get accepted (register succeeds, proving no type-check on register) —
  but proved via pure logic (not worth more live testing) that this can NEVER be used to target
  "admin" specifically: any Mongo query-operator value that matches the string "admin" when used
  later as `{owner: <value>}` against the tickets collection would, by the same logic, ALSO match
  the real "admin" row during the registration pre-check (`findOne({ username: <value> })`),
  which would block registration ("already taken") before we ever get a session. Dead end, don't
  retry this specific idea.

## ⚠️ Stability incident (self-inflicted, resolved)
One test (likely a `__proto__` prototype-pollution probe, or possibly the `q[$ne]=` bracket-array
query) coincided with ALL active sessions on the instance going invalid (plain `/tickets` started
redirecting to `/login` even with a previously-valid cookie) — consistent with the Node process
crashing and restarting (express-session uses an in-memory random secret generated at startup, see
server.js L19, so a restart invalidates every session; MongoDB data was unaffected — our ticket
was still there after re-login). Service recovered on its own within seconds. STOP using
`__proto__`/prototype-pollution payloads and raw bracket-array query keys (`q[$op]=`) against this
target — not worth the shared-instance stability risk for an avenue that hasn't shown promise, and
repeated crashes could read as an infra attack under the CTF's fair-play rules.

## Next angles to try (not yet attempted)
- Study `q` (not `filter`) more: it feeds a `$regex`/`$options` pair per the UI hint text
  ("Search subject...") — try regex metacharacters in plain `q` (not object-ified) to see if
  content/subject regex search silently ignores owner scoping in some edge case (e.g. `q=.*` as a
  normal string value, or injecting `$options` separately as its own top-level query key, e.g.
  `&options=i` if the code builds the regex options from a SEPARATE untrusted query param).
  Low risk since it's all simple strings, no object/proto trickery.
- Timing/blind-boolean side channel: since `filter` additions for `subject`/`content` DO work and
  are presumably ANDed with the forced owner, there's no legitimate way to blind-extract admin's
  ticket this way (the AND keeps us scoped) — deprioritize unless a true bypass of owner is found.
- Re-examine whether `/tickets` (POST, ticket creation) does anything with `subject`/`content`
  that could matter beyond storage (e.g. any admin-side processing/bot that opens new tickets —
  not evidenced in server.js, no notification/mailer code present, so blind-XSS-to-admin is
  unlikely as the intended path, but keep in mind if stuck).
- Ask: is there perhaps a NoSQL operator type that '$type':'string' pre-check model I haven't
  tried for login that differentiates hashed vs plaintext password storage (e.g. if passwords are
  stored hashed and compared via `findOne({username,password})` directly without hashing — meaning
  this challenge might actually want PLAINTEXT password guessing/brute force for a weak admin
  password instead of injection at all. Only try a SMALL number of common/weak guesses if this
  angle is revisited — avoid anything resembling credential brute-forcing per CTF fair-play rules).

Status: PAUSED (not abandoned) — moved on to keep monitoring other challenges; service left in a
healthy, logged-out-but-functional state. Revisit with fresh eyes/more context budget.

## SOLVED ✅ (after organizer "TicketVault updated" announcement, re-tested fresh)
Root cause: `resolveLoginCredentials(req)` sanitizes body-sourced (JSON/urlencoded) input for
NoSQL-injection characters/objects, but does NOT account for Express merging `req.query` — and
Express route handlers read credentials from a source that DOES include query-string values for
this POST route. Sending the injection via the **query string** instead of the body bypasses the
sanitizer entirely:

    POST /login?password[$ne]=x   (URL-encoded: password%5B%24ne%5D=x)
    body: username=admin

Express's default `qs` query parser turns `password[$ne]=x` into `req.query.password = {"$ne":"x"}`
— a live MongoDB operator object — while the body only carries `username=admin`. Wherever
resolveLoginCredentials pulls `password` from, it apparently falls back to / also honors
`req.query`, so `db.collection('users').findOne({ username: 'admin', password: { $ne: 'x' } })`
matches admin (whose real password obviously isn't the literal string "x"), logging us in with NO
real admin credentials needed.

Flag: `CTF{a1428a3ae5db7d74d6c6d1eab1c6296f}` — found directly in the admin's own
"Root cause analysis - incident 2024-03" ticket after logging in as admin. 100 pts (scored as 182
total combined with other solves at submit time — platform may use dynamic/decaying scoring).

Lesson for future challenges: when a body-based NoSQL-injection sanitizer resists every JSON-body
payload, try moving the SAME payload to the query string (or mixing body+query) before concluding
the input is safe — frameworks often read from multiple request-input sources and sanitizers are
easy to apply to only one of them.
