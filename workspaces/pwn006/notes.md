# PWN#006 — Notes

## Setup confirmed
- Target: `169.58.126.107:5009` runs `qjs` (QuickJS CLI) directly on stdin/stdout, no banner/prompt visible.
- **Protocol gotcha**: remote stdout is fully-buffered (not a tty). No output is received until the
  connection's write side is closed (EOF) or the process exits/flushes explicitly. Minimal working probe:
  ```python
  import socket, time
  s = socket.create_connection(('169.58.126.107', 5009), timeout=5)
  s.sendall(b'console.log(1+1)\n')
  s.shutdown(socket.SHUT_WR)   # EOF -> qjs finishes reading stdin, flushes stdout on exit
  time.sleep(2)
  data = s.recv(8192)          # -> b'2\n'
  ```
  For an interactive-style exploit (multi-round leak then write), either keep EOF-ing new connections per
  round, or find a way to force an explicit flush (e.g. if `std` module ends up available, `std.out.flush()`
  — but default interactive/eval mode likely doesn't expose `std`/`os` unless `--std` was passed; verify
  what mode the remote wrapper actually launches qjs in, e.g. `qjs -i` interactive loop vs `qjs` reading a
  script from stdin vs some custom harness).
- Local repro: `./ld-linux-x86-64.so.2 --library-path . ./qjs -e "console.log(1+1)"` works with the provided
  `libc.so.6`/`libm.so.6`.

## Binary info
- `qjs`: x86-64 PIE, stripped, Partial RELRO, NX enabled, **no stack canary**.
- QuickJS version string: `QuickJS version 2024-01-13` (stock Bellard/quickjs, not quickjs-ng — verify which fork if it matters for CVE lookup).
- `libc.so.6`: Debian GLIBC 2.42-13.

## Platform
- CTFd challenge id 31, 150 pts (decaying, min 45), **0 solves** at time of pull — brand new.
- `max_attempts: 3`.

## Next steps (not yet done)
- Identify the exact QuickJS source matching `2024-01-13` and diff/search for known CVEs or obviously-patched-looking bugs (array/typed-array OOB, structuredClone, BigInt, RegExp, Proxy, WeakRef/FinalizationRegistry — common QuickJS bug classes).
- Determine whether the remote wrapper passes any special flags (`--std`, `--bignum`, a preloaded script) — test by probing for `std`/`os`/`BigFloat` global availability remotely.
- Build a local harness (same binary+libc) to fuzz/reproduce candidate bugs before touching the remote target (only 3 attempts).

## STATUS CHECK (2026-10-25 15:11 UTC)
- Platform metadata (id=31): value=136, solves=8, solved_by_me=False, attempts=0, state=visible.
  connection_info `169.58.126.107 5009` unchanged. Attachment now packaged as `handout.zip`
  (previously individual files `qjs`/`libc.so.6`/`libm.so.6`/`ld-linux-x86-64.so.2` were already
  known) — likely the same contents re-zipped, not new material, but not diffed byte-for-byte
  this check (no download performed, per read-only scope).
- **Description CHANGED since last recorded** — it now has an added protocol hint not present in
  the original `challenge.md` text: *"with `nc`, just type your input, then a line with
  `###RUN###`, then whatever you want to send next."* This directly clarifies the stdout-buffering
  gotcha already noted above (remote stdout only flushes on EOF/exit) — `###RUN###` is very likely
  a wrapper-recognized sentinel that triggers an explicit flush/execute without closing the
  connection, enabling a real multi-round interactive session instead of the EOF-per-round
  workaround previously assumed necessary.
- Most promising next concrete step: send a cheap local/remote probe using the `###RUN###` marker
  (e.g. `console.log(1+1)\n###RUN###\n`) to confirm it triggers a mid-session flush, which would
  unlock genuine multi-round exploitation without reconnecting each time.

## `###RUN###` PROBE RESULT (2026-10-25, follow-up session)

**Finding: `###RUN###` does NOT enable a persistent multi-round REPL. It is a one-shot
flush-and-close trigger, functionally equivalent to the previously-used `shutdown(SHUT_WR)` / EOF
technique — just a text sentinel instead of a real socket half-close.** The hint ("type your
input, then `###RUN###`, then whatever you want to send next") describes nc UX convenience
(you don't have to send Ctrl-D), not a new interactive surface.

Evidence (both Python `socket` and real `nc` tested against `169.58.126.107:5009`):

1. `console.log(1+1)\n###RUN###\n` sent on a fresh connection (no EOF/shutdown) → got `b'2\n'`
   back within ~0.35s, confirming the marker *does* trigger an immediate flush without us having
   to half-close the socket ourselves.
2. Sending a **second** payload (`console.log(99)\n###RUN###\n`) on the **same still-open socket**
   right after round 1's response was received: `sendall()` did not raise, but the subsequent
   `recv()` immediately returned `b''` (orderly remote close/FIN). No output for round 2 was ever
   received.
3. Real `nc` reproduction: piped a file containing two `console.log(...)` statements each
   followed by its own `###RUN###` line into `nc 169.58.126.107 5009`. Only the **first** result
   (`2`) was printed to stdout; the second (`console.log(2+2)` → `4`) never appeared, and nc exited
   cleanly (connection closed by remote) — matching the Python test exactly.
4. Sending a round with no `console.log` (e.g. `var __probe_x = 1337;\n###RUN###\n`) still closes
   the connection immediately with **zero** bytes transmitted — confirming the close happens
   unconditionally after the marker is processed, not merely "after output drains."

**Conclusion:** this is still a one-shot-per-TCP-connection challenge. `###RUN###` only changes
*how* you signal "done, run it" (a line a human typing into raw `nc` can send easily) — it does
not change the execution/connection model. No new interactive/stateful attack surface was
unlocked. The actual vuln still has to be a self-contained QuickJS engine bug triggered and
exploited (leak + corrupt + get a shell/read flag) within a **single script sent in one
connection**, since there is no way to accumulate state or do a leak-then-use-offset across two
separate rounds/connections (each connection/process is independent — not verified to be literally
a fresh process per connection, but behaves as a fresh interpreter invocation each time;
`###RUN###` likely just signals the read-the-rest-of-stdin-as-one-script wrapper exactly as EOF
would).

**Additional recon while probing (single-round globals check):**
- `typeof std` / `typeof os` → `undefined undefined`. The `std`/`os` QuickJS modules (which would
  give trivial `os.exec()`/file-read primitives) are **not** exposed by this build/wrapper. No
  shortcut to read the flag via builtin modules — any shell/file-read must come from exploiting a
  memory-corruption bug directly (ROP/shellcode via corrupted engine internals), not from scripting
  a sandboxed API.
- `Object.getOwnPropertyNames(globalThis)` →
  `Object,Function,Error,EvalError,RangeError,ReferenceError,SyntaxError,TypeError,URIError,InternalError,AggregateError,Array,parseInt,parseFloat,isNaN,isFinite,decodeURI,decodeURIComponent,encodeURI,encodeURIComponent,escape,unescape,Infinity,NaN,undefined,Number,Boolean,String,Math,Reflect,Symbol,eval,globalThis,Date,RegExp,JSON,Proxy,Map,Set,WeakMap,WeakSet,ArrayBuffer,SharedArrayBuffer,Uint8ClampedArray,Int8Array,Uint8Array,Int16Array,Uint16Array,Int32Array,Uint32Array,BigInt64Array,BigUint64Array,Float32Array,Float64Array,DataView,Atomics,Promise,BigInt,console,scriptArgs,print`
  — notably **no `WeakRef`/`FinalizationRegistry`** in the global list (stock Bellard QuickJS
  from ~2024 normally has these) — worth double-checking against the exact matching source tag
  when diffing for the injected/patched bug, since their absence could itself be a hint about
  which build options were used, or a red herring from engine config.
- `SharedArrayBuffer` and `Atomics` ARE present — worth keeping in mind as a potential bug surface
  (race/TOCTOU-style engine bugs have existed around Atomics/SAB in various JS engines) even though
  there's only one thread of script execution per connection here.

**Updated next steps:**
- Treat this purely as "one JS script per TCP connection, must self-contained leak+pwn+shell/flag
  read in that single script." Continue the original plan: pull the exact QuickJS source tag
  matching `QuickJS version 2024-01-13`, diff for the injected bug (array/typed-array OOB,
  Proxy, RegExp, BigInt, structuredClone are the classic Bellard-QuickJS CTF bug classes), build
  a local repro harness with the provided binary+libc, and only then spend one of the 3 remote
  attempts.
- No remote flag obtained this session. No exploit built yet — this session was scoped to the
  `###RUN###` probe only, per task instructions.
