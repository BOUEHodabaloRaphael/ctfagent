
## SOLVED (2026-10-15)

**Flag:** `CTF{5e038be14a277c1bf8b912e06de7d943}`

Final working chain, confirmed end-to-end against the live service (144.217.91.111:3000):

1. Prototype pollution on `POST /api/settings` (`merge(user.settings, req.body)`), key
   `__proto__` sent unicode-escaped (`"__proto__"`) in the raw JSON
   body to dodge the WAF's literal-string block. `JSON.parse` still resolves it to the
   real `__proto__` key, so `merge()`'s traversal mutates real `Object.prototype`.
2. Pollute `Object.prototype.outputFunctionName` with the EJS (pre-3.1.10, confirmed
   ejs@3.1.6) identifier-injection gadget. **Between sessions the WAF was updated to also
   block the literal key name `"outputFunctionName"`** (this is new — see below) — bypassed
   the same way, unicode-escaping one character: `"outputFunctionName"`.
3. Gadget body: instead of `throw new Error(...)` (the original plan — doesn't work, see
   below), call `__append(...)` directly (EJS's own render-buffer function) so the command
   output lands straight in the normally-rendered page (HTTP 200), wrapped in
   `try{...}catch(e){return String(e)}` so a nonzero exit doesn't crash the render:
   ```js
   x;__append((function(){try{return process.mainModule.require('child_process')
     .execSync('<cmd>').toString()}catch(e){return String(e)}})());var y
   ```
4. `require` is NOT in scope inside EJS's compiled `new Function(...)` body (module-scoped,
   not global) — use `process.mainModule.require(...)` instead. Confirmed locally that
   `process.mainModule` is only populated when Node is run as a real entrypoint script
   (`node server.js`), not under `node -e` — matches how the challenge actually launches it.
5. Trigger via `GET /notes` (any `res.render()` call); `view cache: false` forces
   recompilation so the polluted identifier takes effect immediately.

### What changed since the 2026-10-06 pause, and what was wrong in that session's notes
- The service being down was real, but so was an **incomplete gadget**: the original
  `exploit.py` used `throw new Error(cmd_output)`, assuming a dev-mode error handler would
  echo the message/stack. The live service runs in production mode and returns a generic
  `Internal Server Error` with no leak — that assumption was never actually verified live,
  it was carried over from the CVE-2022-29078 write-up's PoC style. Lesson: a literal-text
  exfil channel needs confirming per-target, not assumed from the public gadget's PoC.
- The WAF rule set was also hardened: it now blocks the literal key `outputFunctionName`
  too (previously only `__proto__` was blocked). `localsName` is not keyword-blocked, but
  is a messier gadget (used in multiple places in EJS's generated source, including as a
  raw `new Function` parameter-list segment) — not pursued once `outputFunctionName` was
  revived via the same unicode-escape trick already used for `__proto__`.
- `require` alone is undefined inside the compiled template scope on this target (confirmed
  live, "ReferenceError: require is not defined") — had to pivot to
  `process.mainModule.require(...)`.

### Method note for future similar challenges
Before spending live requests iterating on a gadget's exact JS syntax, reproduce the
*exact* vulnerable mechanism offline with the real vulnerable library version
(`npm install ejs@3.1.6` in a scratch dir, call `ejs.render()` after manually polluting
`Object.prototype`, matching the target's execution mode — e.g. run as a real entrypoint
file, not `node -e`, since globals like `process.mainModule` differ). This turned 3-4 wasted
live round-trips (and one rate-limit hit) into a single correct final request once local
repro matched live behavior.
