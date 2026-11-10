---
doc_kind: writeup
title: "battleCTF Qualifier (bugpwn) — TicketVault (NoSQL injection via query-string credential merge)"
category: web
slug: bugpwn-ticketvault-nosql-querystring-bypass
created: 2026-11-10
status: solved
tags:
  - nosql-injection
  - mongodb
  - express
  - sanitizer-bypass
  - idor
source: "ctf.bugpwn.com — battleCTF Qualifier 2026 (challenge id 11, web, 100 pts)"
target: "144.217.91.111:3001 — Node/Express + MongoDB, source server.js + package.json provided"
---
# battleCTF Qualifier — TicketVault

## Challenge Summary

- Node/Express + MongoDB ticketing app. Every user sees only their own tickets; admin's inbox
  holds a "post-mortem" ticket we're not supposed to read.
- Two key helper modules referenced by `server.js` were deliberately **withheld**:
  `./utils/sanitize.js` (`resolveLoginCredentials`, used only on `/login`) and
  `./utils/ticketFilter.js` (`buildScopedFilter`, used on `/tickets/search`) — the vuln lives
  inside one of them.

## Initial Signals

- `/register` does a raw `db.collection('users').findOne({ username })` + `insertOne`, **no type
  validation** on the submitted username — accepting an object there (e.g. `{"$exists":false}`)
  for the username field succeeds, hinting the underlying NoSQL-injection surface is broad.
- `/login` routes through `resolveLoginCredentials(req)` first — looked hardened against the
  obvious JSON-body injection payloads.
- `/tickets/search` advertises an "Advanced filter (JSON, power users)" `filter` query param —
  the obvious bait for a NoSQL filter-injection, but testing showed `owner` specifically could
  never be overridden through it (likely `$and`-wrapped server-side or field-whitelisted),
  while `subject`/`content` narrowing did work.

## Exploit Chain

1. Tried `/login` body-based NoSQL injection (`password: {"$ne": null}`, `{"$gt": ""}`, regex
   bypass as a plain string) — **all failed**, `resolveLoginCredentials` genuinely coerces the
   body-sourced password to a string.
2. Tried `/tickets/search?filter=...` owner-key override (`{"owner":"admin"}`,
   `{"owner":{"$ne":"testuser123"}}`, `{"owner":{"$regex":"^a"}}`, `{}`, `{"$where":"true"}`) —
   all consistently returned only our own ticket. Proved by pure logic that abusing `/register`'s
   missing type-check to register a NoSQL-operator "username" that would match "admin" in the
   tickets collection would *also* match the real admin row in `/register`'s own pre-check
   (`findOne({username})`), blocking registration first — a structural dead end, not worth live
   testing.
3. A `__proto__`/prototype-pollution probe (or a raw bracket-array `q[$ne]=` query) coincided with
   **every active session on the instance going invalid** (likely the Node process crashed and
   restarted — `express-session` generates a random in-memory secret at startup per `server.js`
   L19). Service recovered on its own within seconds; MongoDB data was unaffected. Lesson: stop
   using payloads that risk crashing a shared CTF instance once the technique hasn't shown
   promise — repeated crashes can read as an infra attack under fair-play rules.
4. Paused, then **re-tested after an organizer "TicketVault updated" announcement** with fresh
   eyes. Root cause found: `resolveLoginCredentials(req)` sanitizes **body-sourced**
   (JSON/urlencoded) input against NoSQL-injection characters/objects, but the route handler
   actually resolves the password from a source that **also honors `req.query`** (Express merges
   query-string values into the effective request input for this route). Moving the exact same
   injection payload from the body to the **query string** bypasses the sanitizer entirely:
   ```
   POST /login?password[$ne]=x        (URL-encoded: password%5B%24ne%5D=x)
   body: username=admin
   ```
   Express's default `qs` query parser turns `password[$ne]=x` into
   `req.query.password = {"$ne": "x"}` — a live MongoDB operator object — while the body only
   carries `username=admin`. `db.collection('users').findOne({ username: 'admin', password:
   { $ne: 'x' } })` matches admin (whose real password obviously isn't the literal string "x"),
   logging in as admin with no real credentials needed.
5. Logged in as admin, opened admin's own "Root cause analysis - incident 2024-03" ticket →
   flag directly in the ticket body.

## Key Evidence

```text
POST /login?password[$ne]=x
Content-Type: application/x-www-form-urlencoded

username=admin
```
→ 2xx / redirect to an authenticated admin session; admin's ticket list now visible.

## Dead Ends

- Body-based NoSQL injection on `/login` (JSON and form-encoded) — sanitized correctly, no bypass.
- `filter` param owner-key override on `/tickets/search` — field appears whitelisted/AND-wrapped,
  never budged across `$ne`/`$regex`/empty-object/`$where` attempts.
- Static source leakage (`/server.js`, `/db.js`, `/utils/*.js`, `/.env`) — all 404, no
  `express.static` misconfiguration to exploit.
- `__proto__`/prototype-pollution and raw bracket-array query probes — crashed the shared
  instance once; abandoned as too destructive for the signal they produced.

## Payloads And Commands

```bash
curl -s -X POST "http://144.217.91.111:3001/login?password[$ne]=x" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  --data "username=admin" -c cookies.txt -b cookies.txt -i
curl -s http://144.217.91.111:3001/tickets -b cookies.txt
```

## Flag / Outcome

- `CTF{a1428a3ae5db7d74d6c6d1eab1c6296f}` — 100 pts.

## Reusable Lessons

- When a body-based NoSQL-injection sanitizer resists every JSON-body payload, try moving the
  **identical** payload to the query string (or mixing body+query) before concluding the input is
  genuinely safe — frameworks (Express especially) often merge multiple request-input sources,
  and a sanitizer is easy to apply to only one of them.
- Re-test a paused web challenge after any "updated"/"patched" organizer announcement with a
  genuinely fresh angle — the fix here (described, not literally observed in a diff) evidently
  didn't close the query-string path even though the body path was hardened.
- Avoid prototype-pollution / unusual bracket-array probes against a shared CTF instance once a
  technique hasn't shown promise — the crash-and-recover here cost time without new evidence and
  risked looking like an infra attack.

## Related

- [`php-session-upload-progress-lfi-rce`](../../patterns/web/php-session-upload-progress-lfi-rce.md) — another
  case where a sanitizer only covers one of several equivalent input channels.
