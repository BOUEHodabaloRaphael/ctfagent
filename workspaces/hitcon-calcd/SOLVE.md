# You Got Calc'd? — HITCON CTF 2026

Target: `http://calc.chal.hitconctf.com:<port>/api/calc` (instance per-team, started via
`curl -X POST http://calc.chal.hitconctf.com/api/start -d "token=eb80976f-91e5-445f-ac94-f7ddf42601f3"`).
Instances are short-lived (~5 min window from `expires_at`). Restart whenever the port goes stale
(`Connection refused` on a plain `1+1` request — confirmed this is just instance expiry, not
something we caused, by immediately restarting and re-testing).

## Confirmed baseline (from prior session, not re-tested)
- `POST /api/calc` body `{"expression": "..."}` → `{"result": "..."}` or `{"error": "..."}`.
- Basic arithmetic `+ - * /` with decimals works.
- `1/0` → `{"error":"Exception: Division by zero"}`.
- Letters/parens/functions/`^`/`0x`/ternary/assignment/`;` → `{"error":"Exception: Invalid expression"}`.
- 5000-digit number → `{"result":"inf"}` (no crash).
- 5000x `1+` chain → correct `5001` (iterative, no stack overflow).
- 5000x bare unary `-` → rejected cleanly.

## New findings this session

### 1. Backend language is Dart, not Python
Sending malformed JSON reveals the real exception:
```
POST /api/calc  body: {"expression":
→ 400 {"error":"FormatException: Unexpected end of input (at character 15)\n{\"expression\":\n              ^\n"}
```
This exact message/caret format is `dart:convert`'s `jsonDecode` `FormatException` — a unique Dart
signature. Also:
- missing/non-string `expression` field → `400 {"error":"FormatException: Expected expression"}`
  (a *second*, hand-written `FormatException('Expected expression')` — looks like a custom
  recursive-descent parser's own error, reusing Dart's `FormatException` type).
- Actual grammar/syntax errors inside the expression → `200 {"error":"Exception: Invalid expression"}`
  (plain `Exception`, caught separately from the JSON/type-level `FormatException`s — i.e. there
  are at least two different `catch` sites/exception types in the handler).
- Runtime errors (div by zero) → `200 {"error":"Exception: Division by zero"}`.

Response headers never leak `Server`/`X-Powered-By`; only `x-frame-options`, `x-xss-protection`,
`x-content-type-options: nosniff` (security middleware, doesn't pin a specific framework).

### 2. Numeric formatting smells like native C, via dart:ffi, not Dart's own double.toString()
- `0.1+0.2` → `"0.3"` ; `1/3` → `"0.33333333333333"` (14 significant digits) ; `2/3` →
  `"0.66666666666667"`. This is the classic behavior of C's `printf("%.14g", x)` (precision=14).
  Dart's native `double.toString()` would instead give round-trip/shortest representation
  (e.g. `0.1 + 0.2` → `0.30000000000000004` in plain Dart/JS doubles) — NOT a 14-sig-fig `%g`.
- Large numbers switch to scientific notation exactly where `%.14g` would: `1e16` → `"1e+16"`,
  `1e20` → `"1e+20"` (exponent ≥ precision(14) triggers `%e`-style switch). Dart's own
  `toString()` does not format this way.
- **`inf - inf` → `{"result":"-nan"}`** — lowercase `nan` *with a leading minus sign* is the
  signature of glibc/libc `printf`'s NaN-sign-bit handling on x86 (quiet-NaN propagation from
  `FSUB`/`SUBSD` keeps the sign bit, and glibc's `%f`/`%g` honors it, printing `-nan`). Dart's own
  `NaN.toString()` prints `"NaN"` (capitalized, no sign) — never `-nan`. Python's `str(float('nan'))`
  is `"nan"` without a sign too.
- Conclusion: **the arithmetic evaluator and/or the result formatter is native C code reached via
  `dart:ffi`**, not pure Dart. The Dart layer most likely just does: JSON decode → regex/parser
  validation of the expression string → FFI call into a native `.so` that evaluates + formats the
  double → wraps native errors into Dart `Exception`/`FormatException` for the JSON response.
  This native library is the most promising place for a genuine memory-safety bug ("pwn" per the
  challenge description), since the Dart side itself has been very robust against every parser
  edge case thrown at it so far (no uncaught Dart `Error`/stack trace leak found yet).

### 3. Character-set allowlist is strict and consistent
Confirmed NOT accepted (clean `Invalid expression`, no crash): fullwidth digits (U+FF11),
Arabic-Indic digits (U+0661), NBSP, zero-width space, RTL override (U+202E), NUL byte,
underscores in numbers (`1_000`), scientific notation (`1e10`), `**`, double leading unary signs
(`--1`, `++1` as a *standalone* prefix — though `1++1`/`1--1` DO work, see below), trailing bare
operators (`1+`, `1*`, …), `1..1`, bare `.`, empty string, whitespace-only string.
Confirmed accepted and harmless: embedded `\n`/`\t` (treated as insignificant whitespace),
leading zeros (`007+1` → `8`), leading `+` (`+5` → `5`), trailing `.` (`5.` → `5`).

Inferred grammar: `expr := term (op term)*`, `term := [sign] number` where `sign` is a single
optional `+`/`-` (not stackable) — this cleanly explains `1++1`→`2` and `1--1`→`2` (operator `+`/`-`
followed by a *term* that itself carries one optional sign) while `--1`/`++1` alone fail (no
preceding operator to attach the second sign to) and `1**1` fails (no sign concept after `*`,
and `**` isn't a defined operator).

### 4. Length/perf probing — no crash found yet, but not conclusive
- Single huge number (digits only, no operator): 5,000 / 10,000 / 50,000 / 100,000 chars all
  returned `{"result":"inf"}` in ~1–2.5s. 500,000 chars took ~8.6s. 1,000,000 chars exceeded a
  10s client timeout (unknown whether it would have completed — did not confirm crash; immediately
  re-tested with plain `1+1` afterward and the service was still alive and responsive).
  Timing growth (100k:2.3s, 500k:8.6s) is roughly linear-to-slightly-superlinear, not a sharp
  blowup — inconclusive on whether there's an exploitable algorithmic-complexity bug; should be
  re-measured more rigorously (multiple trials, larger sizes, isolate whether it's the Dart JSON
  decode of a huge string vs. the native numeric parse that's slow).
- Long operator chain `1+1+1+...` (50,000 terms) → correct `50001` in ~2.4s, no issue.
- One apparent "crash" (`Connection refused`) after a 50,000-digit test turned out to be simply
  the per-team instance's natural `expires_at` timeout hit at almost the same moment — confirmed
  by restarting the instance and re-running the same 50,000-digit test cleanly (1.69s, fine).
  **Caution for future sessions: don't over-interpret a `Connection refused` as a crash without
  checking elapsed time against the known `expires_at`.**

### 5. Zero-detection bypass — NOT yet tried
Hypothesis not yet tested: the explicit "Division by zero" guard might check the *parsed double*
value or might check the *literal token text*. If there's a mismatch (e.g. a divisor string that
is textually nonzero but underflows to `0.0` after parsing, or a string that's textually "zero but
weird" like many leading zeros `"000.0"`, `"0.0000...(300 zeros)"`, `"-0"`-variants, concatenated
decimals that parse to exactly 0), it might be possible to reach the raw native division path
without the friendly guard — on some native division semantics that could behave differently
(e.g. integer-division SIGFPE vs. float inf/nan) if the backend mixes integer and float code paths.
Tested so far: `1/-0` and `0.0/0.0` and `0/0.0` are ALL still caught correctly as "Division by zero"
— so the simple cases are closed. Should try: extremely long all-zero decimals, `0` with huge
exponent-like repeated structure (no real exponent since `e` is rejected), and whether the
multiplication/division operand order matters (`0*anything`, `anything*0`, chained `0/0/0`, mixing
very large numbers that round to exactly 0 after some operation before a division by that result —
not possible in one shot since no parens/variables, but consider `1/(huge - huge)`-equivalent via
`inf-inf` → got `-nan` not an error, so NaN is NOT caught by the zero-guard and flows straight to
`{"result":"-nan"}`; worth checking if NaN results can be chained further, e.g. `NaN / 0`-style via
`inf-inf+1` or similar single-expression chains, since current language only allows one pass of
left-to-right binary ops with no parens — so chaining is naturally available: `9999...9-9999...9/0`
etc. NOT yet tried.

## Next steps (for next session / continuation)
1. Try to force a true crash/hang distinctly separated from instance-expiry noise: re-run the
   large-number timing test with a *fresh* instance, far from its `expires_at`, with generous
   client timeouts (30–60s) and immediate liveness re-checks after each probe.
2. Try chained NaN/Inf operations in a single expression (since grammar allows `term (op term)*`
   with no parens, but multiple terms chained left-to-right) to see if a NaN or Inf feeding into a
   *second* operator (e.g. a division) bypasses the "Division by zero" guard or hits a different
   native code path, e.g. `"9"*5000+"-"+"9"*5000+"/0"` (i.e. `(inf-inf)/0` = `nan/0`) and
   `"9"*5000+"/"+"9"*5000+"-1/0"`-style combos — look for any response other than clean
   `{"error":"Exception: Division by zero"}` or a clean numeric result.
3. Try to find the native library's fixed-size buffers indirectly: since the character allowlist
   blocks anything but digits/`.`/`+`/`-`/`*`/`/`/whitespace, buffer-overflow surface is mostly
   about LENGTH, not content. Focus on: (a) a single decimal number with an enormous number of
   digits AFTER the decimal point specifically (not just before) — not yet isolated from the
   "digits before the point" test; (b) numbers crafted to land exactly on `%.14g` rounding-carry
   boundaries (e.g. `9.99999999999995` at varying positions) to see if a carry produces one extra
   output character than a fixed result buffer expects — try many such boundary values
   systematically, not just the two tried so far (`9.9999999999999+0.0000000000001` → clean `10`,
   `9.99999999999999+0.00000000000001` → clean `10`).
4. Look for alternate endpoints/paths exposing the native library directly (checked only `/`,
   `/api/calc` GET/OPTIONS so far → 404 `{"error":"Not found"}` for both). Try `/api/`, `/health`,
   `/debug`, `/metrics`, `/flag`, `/_internal`, `/version`, static file probing (`/index.js`,
   `/server.dart`, `/main.dart`, `.git/`), and directory listing on any discovered static route.
5. Consider race conditions: fire many concurrent huge-number or div-by-zero requests
   simultaneously to see if concurrent access to a shared native buffer (if the FFI call reuses a
   static/global buffer across calls instead of allocating fresh each time) causes corruption
   under concurrency — classic TOCTOU/shared-buffer race in a naive FFI wrapper.
6. If a crash is ever achieved, check immediately whether the HTTP layer returns a stack
   trace/500 with file paths (would hugely help source-level targeting), and whether the
   process auto-restarts (if it does, the crash itself is not directly useful without an
   accompanying leak — need the crash to leak memory/flag, not just DoS).

## Session 2 additions (confirmed facts, big progress on fingerprinting)

### A. Definitively confirmed: native formatting is NOT pure Dart
Installed `dart-sdk` locally (`sudo apt-get install -y dart-sdk`, works on this Kali box) and ran
a comparison script (`/tmp/calc_fuzz/test.dart`) against pure-Dart `double` formatting:
- Pure Dart `(inf-inf).toString()` / `.toStringAsPrecision(14)` → always `"NaN"` (capitalized, no
  sign, ever) — the live server gives `"-nan"` (lowercase, sign preserved). Pure Dart cannot
  produce this; the live value must come from a native library that reads the raw IEEE-754 sign
  bit when formatting (classic glibc/libc `printf("%g")`/`%.14g` behavior on x86 for NaN produced
  by `FSUB`/`SUBSD` of two infinities of opposite effective sign).
- Pure Dart `double.infinity.toString()` → `"Infinity"` — live server gives `"inf"` (lowercase,
  short libc-style form).
- Pure Dart `(1e16).toStringAsPrecision(14)` → `"1.0000000000000e+16"` (keeps trailing zeros,
  14 digits always shown) — live server gives `"1e+16"` (trailing zeros stripped). This is
  exactly how C's `%g` (not `%e`, not Dart's `toStringAsPrecision`) behaves: `%g` drops
  insignificant trailing zeros automatically, `toStringAsPrecision` does not.
- **Conclusion is now solid, not just a hunch: the arithmetic/formatting backend is a native C
  (or C-like) component reached via `dart:ffi`, using something equivalent to
  `snprintf(buf, N, "%.14g", value)`.** This is almost certainly where the actual memory-safety
  bug lives (matches the "Just pwn it" framing — real pwn bug, not a silly regex bypass).
- Checked the low/high exponent switchover boundaries exhaustively (1e-5 through 1e-307 via
  literal decimals and via division to force exponents) and the high end (1e14..1e20, and the
  5000-digit `inf` overflow case) — **all format correctly as expected `%.14g` output, no overflow
  or anomaly found.** So a naive "huge leading-zeros expands into a giant fixed buffer" bug does
  NOT exist — scientific notation kicks in correctly at the %g precision/exponent boundaries in
  both directions. This candidate is now ruled out.

### B. Found a genuine uncaught-error passthrough (info leak primitive, not yet weaponized)
Sending a top-level JSON body that is NOT an object (so the handler's `decoded['expression']`
or equivalent indexing fails) leaks **raw, unwrapped Dart runtime error `toString()`** — no
`"Exception: "` or `"FormatException: "` prefix, HTTP 400:
```
body: ["1+1"]       → {"error":"type 'String' is not a subtype of type 'int' of 'index'"}
body: null          → {"error":"NoSuchMethodError: The method '[]' was called on null.\nReceiver: null\nTried calling: [](\"expression\")"}
body: 42             → {"error":"NoSuchMethodError: Class 'int' has no instance method '[]'.\nReceiver: 42\nTried calling: [](\"expression\")"}
body: true           → {"error":"NoSuchMethodError: Class 'bool' has no instance method '[]'.\nReceiver: true\nTried calling: [](\"expression\")"}
body: "1+1" (bare string) → same TypeError as the array case
body: {"expression":{"a":1}} (nested object) → cleanly caught as FormatException: Expected expression (object value is handled, no crash)
```
This proves the handler structure is (inferred):
```
try {
  ...
} on FormatException catch (e) { return 400, "FormatException: $e" }
on Exception catch (e)       { return 200, "Exception: $e" }       // Invalid expression / Division by zero land here
catch (e)                     { return 400, "$e" }                 // bare catch-all, no prefix — THIS is what we're hitting
```
Dart's bare `catch (e)` (no `on` clause) catches **everything**, including `Error` subtypes
(`TypeError`, `RangeError`, `NoSuchMethodError`, `ArgumentError`, `StateError`, and critically
**`StackOverflowError`**) that the earlier two typed `on` clauses do NOT catch. No stack trace is
included in the leaked text (they're not passing/printing `StackTrace.current` or the exception's
second catch arg), so this alone isn't a source leak — but it confirms ANY Dart-level `Error`
anywhere in the request path gets surfaced as raw `toString()` to us. This is the most promising
non-native lead: if we can find an input that causes a Dart-level `RangeError` or
`StackOverflowError` **inside the expression-parsing/validation code itself** (not just the outer
JSON-type-mismatch trick above), we might get a more informative leak, or trigger something the
native FFI layer doesn't expect (e.g. call it with an already-corrupted/unexpected intermediate
state).

### C. Ruled out this session (tested, all clean/robust)
- Operator-precedence confusion: confirmed **strictly left-to-right evaluation**, no precedence
  (`2+3*4` → `20`, not `14`) — matches real Windows Calculator "Standard" immediate-execution mode,
  just a quirk, not a bug.
- Zero-divisor guard bypass via underflow: `1 / 0.000...(330 zeros)...1` (subnormal underflow to
  real `0.0`) still correctly caught as `Division by zero` — the guard checks the parsed numeric
  value, not the literal text, so no naive bypass.
- Zero-divisor guard bypass via NaN-producing chains: `(inf-inf)/0`, `inf/0` etc. still correctly
  caught as `Division by zero`. `NaN * 0` correctly flows through as `-nan` (not zero-guarded,
  correctly so, since it's multiplication not division).
- Buffer-boundary off-by-one probing: invalid character placed exactly at offsets
  255/256/257, 511/512/513, …, 65535/65536/65537 in an otherwise-valid-looking long digit string —
  always clean `Invalid expression`, no crash at any power-of-two boundary.
- Alternate request shapes: `Content-Type: application/x-www-form-urlencoded` body → clean
  `FormatException` from the JSON decoder choking on non-JSON (confirms body is **always**
  `jsonDecode`'d regardless of `Content-Type` header — no alternate less-sanitized code path via
  content negotiation). `Content-Type: text/plain` with valid JSON body → works fine (content-type
  header is ignored, body is just decoded as JSON unconditionally). Duplicate JSON keys → last
  value wins (standard `jsonDecode` map behavior, not useful). GET with query param → `404 Not
  found` (no alternate GET-based endpoint).
- Large single-number / long-chain timing: re-confirmed instance-expiry false alarm from earlier;
  did not get a chance this session to redo the >500k-digit rigorous timing test with a
  fresh/long-lived instance — **still open, see Next steps below.**

## Next steps (revised after session 2) — highest-value leads, in priority order

Ruled out, do not repeat: operator-precedence tricks, simple zero-guard text/underflow bypass,
NaN-into-division bypass, power-of-two buffer-boundary off-by-ones, content-type/body-shape
tricks (body is always `jsonDecode`'d regardless of header), scientific-notation exponent-switch
edge cases from 1e-307 to 1e20 (all correct `%.14g`-style output, no overflow found).

1. **Decimal-point-heavy numbers specifically (many digits AFTER the `.`, not before).** All
   large-digit tests so far used integer-looking strings (`"9"*n`). Never isolated "many digits
   after the decimal point with a SHORT integer part" (e.g. `"1." + "9"*100000`). If the native
   code parses the fractional part via a different code path than the integer part (common in
   hand-written parsers), this is untested territory.
2. **Systematic rounding-carry boundary fuzzing against the `%.14g` formatter.** Generate values
   of the form `D.DDDDDDDDDDDDD5` (14 significant digits ending in 5, forcing a round-to-even/
   round-up carry) at many exponents (achievable via division since literal `e` notation is
   blocked), and diff each live response against Python's local `'%.14g' % value` to catch any
   case where the native formatter deviates from true libc `%.14g` semantics — a deviation would
   be the signal of a bug in a custom/ported reimplementation rather than real glibc.
3. **Trigger a Dart-level `Error` (not `Exception`) from *inside* the expression grammar itself**,
   not just via the outer JSON-body-shape trick (already proven to leak raw `NoSuchMethodError`/
   `TypeError` text — see part B above). The outer trick proves a bare `catch (e)` exists that
   surfaces ANY uncaught Dart `Error` as raw text; the goal now is an expression string that makes
   the *parser itself* throw a `RangeError`/`StackOverflowError`, which might leak more, or show
   the native FFI call received a bad/partial argument before throwing.
4. **Concurrency/race**: fire many simultaneous huge-number or boundary-value requests at once
   (e.g. `xargs -P50` over curl) to see if a shared/static buffer in the native FFI layer gets
   corrupted under concurrent access — classic TOCTOU in a naively-written FFI wrapper reusing a
   global scratch buffer instead of allocating fresh per call. Not attempted at all yet.
5. Re-verify the >500k-digit timing anomaly properly with a **fresh instance immediately after
   `/api/start`** (no `expires_at` ambiguity), 60s client timeouts, sizes 1M/5M/10M digits —
   last attempt's 1M-digit request hit a 10s client timeout with unknown server-side outcome
   (follow-up liveness check was OK, but that only proves recovery, not what happened during).
6. Untried endpoints: `/api/`, `/health`, `/debug`, `/metrics`, `/flag`, `/_internal`, `/version`,
   `.git/`, `/main.dart`, `/server.dart`, `/packages/`.
7. If a crash is ever achieved: check immediately for a stack trace/500 with file paths, and
   whether the process auto-restarts. A plain crash/DoS alone does not get the flag — need an
   accompanying info leak or an actually-steerable memory corruption.

## Session 2 additional negative results (items from the revised Next-steps list, now tried)
- **Decimal-point-heavy numbers** (`"1." + "9"*100000`, i.e. huge fractional part with tiny
  integer part): rounds correctly to `2` (nearest double), no crash, no anomaly. Ruled out.
- **Long operator chains at real scale** (not just 5000/50000 — tried 100000, 300000, and
  1,000,000 terms of `1+1+1+...`): all return the mathematically correct result, no crash.
  Timing is roughly linear-ish but with real overhead: 100k terms ≈ 4s, 300k ≈ 15.6s, 1M terms ≈
  44.8s. Slower than strictly linear but nowhere near a quadratic blowup (1M is ~3.3x the size of
  300k but only ~2.9x the time) — looks like real but unremarkable per-token processing cost, not
  an algorithmic-complexity bug. The service stayed fully alive and correct throughout, including
  immediately after the 44.8s request. **Ruled out as a crash vector**, though note it IS a mild
  self-inflicted slow-request DoS if someone wanted to stall one instance's single connection.
- **Concurrency/race condition probing** (new this round, item 4 from the list): fired (a) 90
  concurrent small/fast requests (9 distinct digit-repunit sums × 10 rounds) and (b) 10 concurrent
  *slow* requests (each a distinct starting value + an 80,000-term `+1` chain, ~20-25s each, run
  all at once via `xargs -P 10`/`-P 90`) and diffed every response against its own expected value.
  **Zero cross-talk/corruption in both cases** — every response matched its own request exactly,
  even under heavy concurrent load on the slow native-processing path. No evidence of a shared
  static buffer being overwritten across concurrent FFI calls. **Ruled out** (at least at this
  concurrency level — did not try drastically higher, e.g. 500+ concurrent, due to time limits).
- Misc small-scale parser edge cases (`"1.+1"`, `"1+*1"`, `"1*/1"`, `"1/+1"`, `"1-*1"`, `"-.5+1"`,
  `.5`/`-.5`, 5000-char whitespace-only string, `1/0.000...(5000 zeros, no trailing nonzero)`,
  `"1.1.1.1"`, `"1+1."`, `".+1"`): all behave exactly as a sane hand-written left-to-right
  calculator grammar would — either a correct numeric result or a clean `Invalid expression`.
  No anomalies. These are now exhausted as a search space.

## Instance-management notes for continuation
- Each `/api/start` gives ~300s before `expires_at`; right after stopping a previous instance it
  may answer `{"error": "Instances are busy; retry shortly"}` — wait ~5s and retry.
- A sudden `Connection refused` can be either a real crash or just instance expiry — always
  cross-check wall-clock time against the known `expires_at` before concluding "we crashed it"
  (this cost real confusion in session 2: a 50k-digit test's apparent crash was just the instance
  expiring at almost the same moment).
- `dart-sdk` is now installed on this box (`sudo apt-get install -y dart-sdk`) — useful for
  diffing real Dart behavior against the live server, as done in part A above. Scratch script at
  `/tmp/calc_fuzz/test.dart` (not committed, this is a throwaway comparison tool).

## Status: NOT SOLVED YET — no RCE/flag found after 2 sessions (~5 instance windows, ~25+ min of
live server time total).

Confirmed facts: Dart (`shelf`-style) HTTP layer + a native C FFI library doing the actual
arithmetic/formatting (proven via local Dart-vs-live diff in part A, not just inference); strict
character allowlist on the expression string (digits, `.`, `+`, `-`, `*`, `/`, whitespace only —
no letters/parens/unicode-digits/underscores/scientific-notation); strictly left-to-right
evaluation with no operator precedence; a bare `catch (e)` somewhere that leaks raw
uncaught-Dart-error `toString()` for malformed JSON body *shapes* (proven in part B), but not yet
triggered from *inside* expression parsing itself. No crash, no stack trace, no flag yet.

What has been thoroughly ruled out across both sessions: operator-precedence tricks, zero-guard
bypass (text or underflow based), NaN/Inf chaining into the zero guard, power-of-two buffer
boundaries, alternate content-types/body shapes, scientific-notation exponent switchover at every
tested magnitude from 1e-307 to 1e+20, decimal-point-heavy numbers, long operator chains up to 1M
terms (scales ~linearly, no crash), and concurrency/race conditions up to ~90 simultaneous
requests (zero cross-talk observed, both on fast and slow/heavy requests).

**Remaining genuinely untried leads** (highest value first):
1. Systematic rounding-carry-boundary diff-fuzzing of the `%.14g` formatter against a local
   Python/Dart oracle (described above) — only two ad hoc boundary values were tried, not a real
   sweep across exponents.
2. Finding an expression that makes the *parser itself* throw an uncaught Dart `Error`
   (`RangeError`/`StackOverflowError`) to see what the bare `catch (e)` leaks from inside actual
   expression evaluation (only triggered this catch via the outer JSON-body-shape trick so far,
   never from a weird-but-charset-valid expression string).
3. Endpoint/path enumeration beyond `/`, `/api/calc` (GET/OPTIONS/query-param — all 404): never
   tried `/health`, `/debug`, `/metrics`, `/flag`, `/version`, `.git/`, `/main.dart`, `/packages/`.
4. Much higher concurrency (500+) or concurrency specifically paired with huge single numbers
   (not just long chains) — only chain-based slow requests were tested concurrently.
5. A real decompiled look at the Dart/native binary if it's ever reachable (e.g. via a path
   traversal or source-leak endpoint) — all conclusions so far are blackbox-inferred from
   response behavior, never confirmed against actual source/binary.

This is a genuinely well-built challenge backend — it has survived two full fuzzing sessions
without a single crash, uncaught internal error from the expression grammar, or race condition.
The bug is likely narrow and specific (a particular formatting edge case, or a specific parser
state only reachable with a precise charset-valid string), not a broad class of input. Recommend
next session invest in automated/scripted diff-fuzzing (item 1) rather than more manual spot
checks, since manual probing of individual edge cases has been exhausted without a hit.
