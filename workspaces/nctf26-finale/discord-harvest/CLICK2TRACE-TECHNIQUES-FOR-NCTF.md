# Click2Trace CTF — Technique Digest for NCTF26 Finale

Built from 15 downloaded writeups in `downloads/click2trace/` (manifest: `click2trace-SOURCES.md`).
Flag format for all challenges: `C2T{...}`. Every claim below cites its source filename.
All source files were read-only; no snippet was executed.

> OSINT note: the external OSINT writeup set
> (`medium.com/@mehdibenfaidia/click2trace-ctf-osint-writeups-eebc84290d78`)
> returned **HTTP 403 (permanent, Medium blocks automated fetches)** and could not be
> summarized. It needs a logged-in browser copy or a pasted text export to add. A generic
> OSINT checklist stub is kept at the end so the section exists for the finale.

---

## WEB

### 1. Secterm — AI Agent Security  (`web_Secterm_AI_agent.txt`)  [HARD — HIGHEST FINALE PRIORITY]

- **Vuln/mechanism:** Indirect prompt injection / side-channel instruction smuggling. The
  "agent" is a deterministic rule-based state machine (`init → escalation_pending →
  vault_authorized`). It parses attacker-controlled *data* fields — the support-ticket body
  and the operator profile **bio** — for intent keywords and treats them as commands, exactly
  like direct chat input. Direct requests for the vault are refused (`/vault*` = 403, chat ask
  = refused), but the same intent planted in side-channel fields drives the state machine.
- **Exploit technique + tools:** Walk the state machine through its own narrated requirements
  (the refusal messages are the walkthrough). (1) `GET /greeting` → read per-session `Briefing
  reference` nonce. (2) `POST /ticket` with body containing escalation keywords (`request`,
  `approve`, `escalate`, `authorize`, `records access`) **and** the nonce → `escalation_pending`.
  (3) `POST /profile` set bio with confirmation language (`confirm/approve/escalation/ticket`)
  **plus** a fetch directive naming the target → primes the `escalate` + `fetch_url` tools.
  (4) `GET /greeting` again → agent flips to `vault_authorized`, then calls
  `fetch_url("http://vault.internal/vault/record")` (an SSRF-equivalent internal-reaching tool
  capability; a `169.254.169.254` metadata decoy is planted on that path) and the flag returns
  in the tool result. Tools: `curl` + cookie jar only. Flag `C2T{1nj3ct3d_thr0ugh_th3_s1d3_ch4nn3l}`.
- **Reusable for NCTF finale:** This is the direct analogue of the `nctf26-agent-tool-abuse`
  challenge. Key moves: (a) enumerate **every field the agent reads back about you** (bio,
  ticket, uploaded doc, display name) as injection points, not just the chat box; (b) harvest
  the state-transition keyword vocabulary from the agent's own refusal/guidance text; (c) carry
  any required nonce/reference through each step; (d) treat an agent `fetch_url`/tool as an SSRF
  primitive to internal hosts — look for a `*.internal` target and a metadata-endpoint decoy;
  (e) fold confirm + fetch directives into ONE field to minimize round-trips.

### 2. Reading Between The Glyphs — font-stego → SSRF  (`web_Reading_Between_The_Glyphs.md`)

- **Vuln/mechanism:** An internal URL + access key are hidden in a web font via **GSUB `calt`
  (contextual alternates) shaping**, not in the raw `cmap`. Reading the cmap directly
  (`getBestCmap()`) yields a **decoy** URL/key; the real values only appear once the font's
  ligature/shaping substitutions are applied ("shape, don't scrape"). Chained into a `/preview`
  SSRF that fetches the internal metadata sidecar server-side.
- **Exploit technique + tools:** Fetch `/static/rebel-glyphs.woff2` + the PUA specimen runs
  (`/static/totem.txt`, `/static/totem-key.txt`). Decompress woff2→TTF (HarfBuzz can't read
  woff2), then **shape** each PUA run with uharfbuzz (applies `calt` like a browser) and map
  output glyph IDs back to Unicode → real internal URL + key. Then
  `GET /preview?url=<internal_url>?key=<key>` → server-side fetch returns the flag. Tools:
  `fontTools`, `brotli`, `uharfbuzz`, `requests`. Flag `C2T{glyphs_h1d3_th3_g4t3w4y}`.
- **Reusable for NCTF finale:** When a font/glyph artifact is handed over, do not trust the
  cmap — render/shape it. GSUB `calt`/ligature substitutions can encode a different string than
  the codepoints. Pattern applies to any font-based stego and to `/preview`-style SSRF where the
  server fetches an attacker-reconstructed internal URL (carry the key through the query).

### 3. Order Of Operations — operator-precedence cookie forgery  (`web_Order_Of_Operations.md`)

- **Vuln/mechanism:** The `access_token` cookie is a **client-computable function of leaked
  response-header values**. The server scatters inputs across headers on different routes and
  expects `answer = a + b*c` (multiply-before-add precedence) then a storage transform
  `token = answer XOR a`. No server-side secret — fully forgeable.
- **Exploit technique + tools:** Read `X-Alpha` (`/`), `X-Beta-Enc` (`/products`, decode per
  `X-Decode` = base36), `X-Gamma` (`/contact`). Compute `a + b*c`, XOR with `a`, set
  `access_token=<token>`, `GET /vault` → flag in `<pre>`. Tools: `curl`, shell arithmetic.
  Flag `C2T{4dd1ng_up_4cr0ss_th3_w1r3}`.
- **Reusable for NCTF finale:** Collect response headers across *all* routes, not just the one
  you're attacking — a token/cookie may be a deterministic formula over them. Watch operator
  precedence and a trivial XOR/encode storage transform. Classic "forgeable signed-ish cookie"
  where the signing is really just arithmetic.

### 4. Deprecated, Not Deleted — GraphQL field-suggestion recovery  (`web_Deprecated_Not_Deleted.md`)

- **Vuln/mechanism:** GraphQL introspection is OFF and the "leaked" SDL dumps are decoys, but
  the server's **field-suggestion ("Did you mean?") error oracle** still leaks the hidden field
  name. The access token for that field is **derived** (XOR of a v3-bundle constant against the
  live `systemStatus.region` value), not a grep-able literal.
- **Exploit technique + tools:** Probe a stale name `{ legacyExport }` → error says *"Did you
  mean 'legacySecret'?"*. Version-walk to `/static/app.v3.bundle.js` (or `/archive`) to read
  the derivation `token = unpack(atob(T), region)`. Query `{ systemStatus { region } }` for the
  XOR key, derive `atob(T) XOR region`, then `{ legacySecret(token:"<derived>") }` → flag.
  Tools: `requests`, regex, base64. Flag `C2T{d3pr3c4t3d_but_n0t_d3l3t3d}`.
- **Reusable for NCTF finale:** When GraphQL introspection is disabled, use the field/argument
  **suggestion oracle** to recover hidden schema names one guess at a time. Then hunt old/deprecated
  JS bundles (`.v3.bundle.js`, `/archive`) for client-side token derivation logic rather than a
  static secret.

### 5. Ghosts of 2003 — soft-delete IDOR + semantic cron gate  (`web_Ghosts_of_2003.txt`)

- **Vuln/mechanism:** Two weaknesses. (a) IDOR: a soft-deleted forum post is gone from the index
  but `/post?id=` has no visibility check — a **gap in sequential ids (id 113 missing)** is the
  tell. (b) A "semantic" access gate on `/cron-status` that releases content only when the exact
  cron expression of a hidden schedule is supplied — recovered by reverse-engineering a member's
  posting timestamps.
- **Exploit technique + tools:** `GET /post?id=113` → rot13-encoded fragment 1 (shift value 13
  confirmed from neighbor posts 111/114). Spot username `tnocrab` = anagram of `crontab`; their
  posts land at `:00` on odd hours → cron `0 1-23/2 * * *`. `GET /cron-status?cron=0 1-23/2 * * *`
  → fragment 2; concatenate. Tools: `curl`, rot13. Flag `C2T{d1gg1ng_thr0ugh_th3_4rch1v3s}`.
- **Reusable for NCTF finale:** Enumerate sequential object ids and look for gaps (soft-deleted
  records remain fetchable). Treat obvious anagram usernames/labels as hints. Endpoints gated on a
  value reverse-engineered from side channels (timestamps, usernames) are open endpoints with a
  puzzle on top, not real access control.

### 6. Right Here, Right Now — SVG-embedded PoW handshake  (`web_Right_Here_Right_Now.txt`)

- **Vuln/mechanism:** `/data` requires an unkeyed "proof of work": `sha256(tok:phrase)`, where
  `tok` is a session-bound salt from `/challenge` and `phrase` is hidden inside a **base64-embedded
  SVG `<text>` element** on the homepage. Time-bound to the current minute (±1). No secret —
  both inputs are retrievable unauthenticated.
- **Exploit technique + tools:** `GET /challenge` (keep cookie) → `tok`. Decode the homepage
  `data:...;base64,` SVG → read phrase from `<text>`. `sha256("<tok>:<phrase>")` lowercase hex,
  submit as `X-PoW` + `X-PoW-Token` headers to `/data` within the window. Tools: `curl`,
  `base64`, `sha256sum`. Flag `C2T{t1m3_b0und_h4sh_h4ndsh4k3}`.
- **Reusable for NCTF finale:** Decode every base64-embedded asset (SVG/PNG data URIs) for hidden
  text. Script homemade PoW/handshake schemes end-to-end (mint→extract→hash→submit in one pass)
  to beat short validity windows; the colon-join format `tok:phrase` is a common convention.

### 7. Schrödinger's File — PNG/ZIP polyglot + stateful unlock  (`web_Schrodingers_File.txt`)

- **Vuln/mechanism:** Upload filter demands a file valid as **both PNG and ZIP** simultaneously
  (structural/magic-byte validation only, not intent). PNG parses front-to-back to `IEND`; ZIP
  scans backward for the EOCD — they don't contend for the same bytes, so one file satisfies both.
  Followed by a multi-round handshake where the final gate is derived from **client-supplied image
  dimensions**.
- **Exploit technique + tools:** Build `[PNG sig][IHDR]...[IEND][ZIP local headers][central dir][EOCD]`.
  Upload → capture `X-Image-Nonce`. Embed nonce as a PNG `tEXt` chunk (`Comment=<nonce>`) before
  `IEND`, re-upload → get `X-Unlock-Token`. Submit `unlock.txt` = `sha256(f"{token}:{W}x{H}")`
  (W×H from IHDR, 1×1) alongside the polyglot → flag. Tools: manual PNG/ZIP byte assembly,
  `sha256`. Flag `C2T{tw0_f1l3s_0n3_byt3str34m}`.
- **Reusable for NCTF finale:** Front-anchored vs back-anchored format pairs (PNG/ZIP, GIF/ZIP,
  JPEG/ZIP) bypass "does this parse as X" upload filters. When a handshake derives its gate from
  values read out of the file you uploaded (dimensions, metadata), you control both sides — script it.

### 8. Liar's Manifest — Referer-gating + robots red-herring + knock handshake  (`web_Liars_Manifest.txt`)

- **Vuln/mechanism:** An internal export endpoint is "protected" by a `Referer` header check.
  The expected Referer is split: gateway host in a `robots.txt` comment, path fragment as a
  **ROT13 string in an `/about` HTML comment**. Even correct, the first request returns 403 with a
  one-time `X-Knock` nonce that must be echoed as `If-Match` on a follow-up (replayable, no identity
  binding).
- **Exploit technique + tools:** `robots.txt` → `# gateway-host: portal.th3r3bel.internal`;
  `/about` → `<!-- rot13('nhgu') -->` decodes to `auth`; assemble
  `https://portal.th3r3bel.internal/auth`. Request `/internal/legacy-export` with that `Referer`
  → grab `X-Knock`; replay with `If-Match: <nonce>` → flag. Tools: `curl`, `tr` (rot13).
  Flag `C2T{r0b0ts_d0nt_4lw4ys_t3ll_th3_truth}`.
- **Reusable for NCTF finale:** Read `robots.txt` and low-traffic static pages (`/about`) closely
  for split secrets; client headers (`Referer`) are never auth. A nonce handed to anyone presenting
  the right header is just an extra scripted round-trip, not a control.

### 9. Declassified — strip-once path-traversal filter bypass  (`web_Declassified.txt`)

- **Vuln/mechanism:** `GET /read?doc=` serves vault files and blocks traversal by a **single,
  non-recursive `doc.replace("../","")`** with no canonicalization/containment check. The payload
  `....//` collapses to `../` *after* the one-pass strip, reconstituting the traversal token the
  filter just removed.
- **Exploit technique + tools:** `....//....//` → `../../` post-filter. `GET
  /read?doc=....//....//ops/HANDOFF.txt` (breadcrumb naming `private/flag.enc` + encoding order),
  then `/read?doc=....//....//private/flag.enc` → `base64(atbash(flag))`; base64-decode then atbash
  (self-inverse) → flag. (Direct `../../` is fully stripped → 404, hiding the bug.) Tools: `curl`,
  base64, atbash. Flag `C2T{tr4v3rs3_th3_n41v3_f1lt3r}`.
- **Reusable for NCTF finale:** Against any single-`replace()` traversal filter try self-
  reconstructing payloads (`....//`, `..././`, `....\/`). Naive `../../` returning 404 is a sign the
  strip works once — escalate to the overlapping form. Look for a HANDOFF/README breadcrumb naming
  the real file + its obfuscation (base64/atbash/rot).

---

## REVERSE

> Cross-cutting pattern (rev 18–22): **five of the six rev challenges are the same
> `SBOX[input[i]] ^ keystream[i] == target[i]` relation** (or an invertible register-VM op chain)
> re-skinned across runtimes. Once you recognize it, the solve is always: extract the 3 tables
> (256-byte S-box, 16-byte keystream, 16-byte target), build `inv_sbox`, and compute
> `input[i] = inv_sbox[target[i] ^ keystream[i]]`. This "same core across many VMs/runtimes" is the
> single most finale-reusable rev insight here.

### 10. Linear Descent — self-checksum GF(2) linear system  (`rev_17-linear-descent.md`)  [HARD]

- **Vuln/mechanism:** Static x86-64 ELF (hand-written asm, no libc). A routine in a custom
  `text_check` section sums its own bytes to derive key `k`, XOR-decrypts a `data_mt` section into
  a **128×128 bit matrix M + 128-bit target T over GF(2)**, and validates input `x` iff `M*x = T`.
  The self-checksum prevents patching.
- **Exploit technique + tools:** Extract `text_check` + `data_mt` from the ELF; `k =
  sum(text_check) & 0xFF`; XOR-decrypt; parse M (2048 B) and T (16 B); solve `M*x=T` by **Gaussian
  elimination over GF(2)**. Tools: Python (section extraction, GF(2) solver). Example
  `C2T{900cc297a83a61dc98b8c22a2482cc08}`.
- **Reusable for NCTF finale:** When a binary checks its own bytes to derive a key, don't patch —
  replicate the checksum statically. A verifier that is a linear system over GF(2) is solved by
  Gaussian elimination, not brute force.

### 11. Mirror — custom register VM, self-checksum + anti-debug  (`rev_18-mirror-vm.md`)  [VM/BYTECODE]

- **Vuln/mechanism:** Static x86-64 ELF implementing a **custom register VM**. `vm_text` =
  interpreter, `vm_data` = S-box + bytecode + target. A self-checksum `kc = sum(vm_text)&0xFF`
  seeds (a) `ptrace(PTRACE_TRACEME)` **anti-debug** that alters `kc` if traced, (b) a **rolling
  XOR-chain** decrypt of the bytecode (`plain[i]=enc[i]^rk; rk=enc[i]`, `rk0=kc`), and (c)
  instruction decode `op = code[pc] ^ (kc&7)`. 6 **bijective** ops: XORC/ADDC/ROL/SWAP/SBOX/HALT.
- **Exploit technique + tools:** Extract sections statically (avoid the ptrace path), compute `kc`,
  do the rolling-XOR decrypt, parse 3-byte `(op,a,b)` instructions, then **run the op chain
  backward from the target state** (each op is invertible: XOR self-inverse, ADDC→subtract,
  ROL→ROR, SWAP self-inverse, SBOX→inv_sbox). Tools: Python. Example
  `C2T{4726674a9b7eb46aa9cc2abfb3c0b543}`.
- **Reusable for NCTF finale:** The canonical custom-VM method — identify the instruction format,
  decode the op table, confirm every op is bijective, then invert the program from the target
  rather than searching inputs. Solve statically to sidestep ptrace anti-debug; the checksum that
  seeds decryption is just `sum(section)&0xFF`.

### 12. YARV Whisperer — Ruby YARV bytecode reading  (`rev_19-yarv-whisperer.md`)  [HARD, VM/BYTECODE]

- **Vuln/mechanism:** A Ruby loader (`check.rb`) hides the real logic in a **Base64-marshaled
  `RubyVM::InstructionSequence` (YARV bytecode)**, pinned to Ruby 3.2.x, behind dynamic method
  calls. The sequence embeds an array `D` = 256-byte S-box + 16-byte keystream + 16-byte target,
  and the verify loop is the usual `SBOX[input[i]] ^ keystream[i] == target[i]`.
- **Exploit technique + tools:** Load + disassemble the blob with
  `RubyVM::InstructionSequence.load_from_binary(Base64.strict_decode64(BLOB))`, extract the
  288-int array, then `input[i] = inv_sbox[target[i] ^ keystream[i]]`. Tools: Ruby (ISeq
  disassembly), Python (invert). Example `C2T{2f067ec57c4778e412efdb83f322cbcb}`.
- **Reusable for NCTF finale:** For a Ruby challenge hiding logic in a marshaled blob, use the
  built-in `RubyVM::InstructionSequence.load_from_binary` + `.disasm` to read YARV bytecode rather
  than guessing — the constants (S-box/keystream/target) are sitting in the instruction array.

### 13. The Mill — WASM register VM  (`rev_20-the-mill.md`)  [VM/BYTECODE]

- **Vuln/mechanism:** `check.wasm` is a **control-flow-flattened register VM** compiled to
  WebAssembly. The data segment (offset 256) holds 256-byte S-box + 1024-byte bytecode + 16-byte
  target; 3-byte instructions `op,a,b` with the same 6 bijective ops (XORC/ADDC/ROL/SWAP/SBOX/HALT)
  as Mirror.
- **Exploit technique + tools:** Extract the WASM data segment, parse the instruction stream, build
  `inv_sbox`, and **invert the op chain from the target state** (identical reversal logic to
  rev_18). Tools: WASM data-segment extraction, Python. Example
  `C2T{f3055ffad8c59dc7ed3827f863937ebe}`.
- **Reusable for NCTF finale:** WASM VMs store their bytecode/tables in a data segment — dump it and
  apply the same custom-VM reversal method. The op semantics here are byte-for-byte the same as the
  native ELF VM (Mirror), so recognizing one solves the other.

### 14. Kernel Oracle — eBPF static RE  (`rev_21-kernel-oracle.md`)  [KERNEL]

- **Vuln/mechanism:** An **eBPF relocatable object** (`check.bpf.o`, `clang -target bpf`) holds the
  verifier in a `socket` program; `.rodata` = 256-byte S-box + 16-byte keystream + 16-byte target,
  `.bss` = 16-byte input. Loop is `SBOX[input[i]] ^ keystream[i] == target[i]`. Runs in kernel
  space, so **static RE is the intended path (no loading required)**.
- **Exploit technique + tools:** Read `.rodata` from the ELF (e.g. objcopy/pyelftools), split into
  S-box/keystream/target, then `input[i] = inv_sbox[target[i] ^ keystream[i]]`. Tools: ELF section
  extraction, Python. Example `C2T{e632d5a68ab2ad371b6dc46c13265cb8}`.
- **Reusable for NCTF finale:** Don't try to load a kernel/eBPF object — treat `.bpf.o` as a static
  ELF and pull constants from `.rodata`. "Kernel oracle" style challenges usually reduce to reading
  a section, not running the program.

### 15. Threaded — Forth / RPN verifier  (`rev_22-threaded.md`)

- **Vuln/mechanism:** A Forth script (`check.fs`, runs in `gforth`) defines `SBOX` (256),
  `XK` (16-byte keystream), `TGT` (16-byte target); the `verify` word loops 16× computing
  `SBOX[INP[i]] xor XK[i] <> TGT[i]` on the data stack (RPN) — the same core relation.
- **Exploit technique + tools:** Parse the three tables straight out of the Forth source (no
  execution needed), then `input[i] = inv_sbox[tgt[i] ^ xk[i]]`. Tools: text parsing, Python.
  Example `C2T{a7e047a7d80eca4b8fa1d81ac92157c5}`.
- **Reusable for NCTF finale:** Esoteric-runtime verifiers (Forth/RPN, and the VM family above)
  usually just transliterate a simple byte relation — read the source/bytecode for the S-box +
  keystream + target tables instead of trying to execute the exotic stack machine.

---

## OSINT

Source `medium.com/@mehdibenfaidia/click2trace-ctf-osint-writeups-eebc84290d78` was **not
retrievable (HTTP 403, Medium blocks automated fetches)**, so no per-challenge Click2Trace OSINT
techniques could be extracted. To fill this in for the finale, paste a text export of the article
or supply a mirror. Generic OSINT methodology to fall back on in the meantime:

- Reverse image search (Google Lens / Yandex / TinEye) + EXIF/GPS extraction (`exiftool`) for
  geolocation.
- Username enumeration across platforms (Sherlock/WhatsMyName) and social-media pivoting.
- Wayback Machine / archive.today for deleted or historical pages; `waybackurls`.
- DNS/WHOIS history, subdomain enumeration, certificate transparency (crt.sh).
- Shodan/Censys for exposed services; metadata in documents (author/software fields).

---

## Reusable-Patterns Checklist (finale quick-reference)

WEB
- [ ] **AI-agent prompt/tool-abuse chain** (`web_Secterm_AI_agent.txt`): enumerate every field the
      agent reads back (bio/ticket/doc), harvest state-transition keywords from its own refusals,
      carry the nonce, drive `escalate`→`fetch_url` as an SSRF to a `*.internal` host (watch for a
      169.254.169.254 decoy). **Primary model for `nctf26-agent-tool-abuse`.**
- [ ] **GSUB `calt` font-shaping stego** (`web_Reading_Between_The_Glyphs.md`): shape the font
      (uharfbuzz), don't scrape the cmap (decoy); feed the shaped internal URL+key into a `/preview`
      SSRF.
- [ ] **Operator-precedence cookie forgery** (`web_Order_Of_Operations.md`): token = deterministic
      arithmetic (`a+b*c`, then `XOR a`) over leaked response headers across routes.
- [ ] **GraphQL field-suggestion recovery** (`web_Deprecated_Not_Deleted.md`): introspection-off ⇒
      use "Did you mean?" oracle; derive token from an old JS bundle XOR a live field.
- [ ] **Soft-delete IDOR + semantic gate** (`web_Ghosts_of_2003.txt`): enumerate id gaps; anagram
      usernames (`tnocrab`=crontab); reverse-engineer a cron/schedule from timestamps.
- [ ] **Base64-embedded asset + homemade PoW** (`web_Right_Here_Right_Now.txt`): decode SVG/PNG data
      URIs for hidden text; script `sha256(tok:phrase)` handshakes inside their time window.
- [ ] **Front/back-anchored polyglot upload bypass** (`web_Schrodingers_File.txt`): PNG+ZIP (also
      GIF/JPEG+ZIP) defeats "parses as X" filters; handshake gates derived from your own file's
      metadata are scriptable.
- [ ] **robots/Referer red-herring + knock handshake** (`web_Liars_Manifest.txt`): split secrets in
      robots.txt + rot13 HTML comments; echo `X-Knock`→`If-Match`.
- [ ] **Strip-once traversal bypass** (`web_Declassified.txt`): `....//` reconstitutes `../` after a
      single non-recursive `.replace()`; chase HANDOFF breadcrumbs + base64/atbash encoding.

REVERSE
- [ ] **One core relation across many runtimes** (`rev_18`–`rev_22`):
      `input[i] = inv_sbox[target[i] ^ keystream[i]]` — extract (256-byte S-box, 16-byte keystream,
      16-byte target) from ELF VM / WASM / Ruby YARV / eBPF `.rodata` / Forth and invert. Recognize
      once, solve all.
- [ ] **Custom-VM reversing method** (`rev_18-mirror-vm.md`, `rev_20-the-mill.md`): decode the
      instruction format + op table, confirm ops are bijective, invert the program backward from the
      target; solve statically to skip ptrace anti-debug.
- [ ] **Ruby YARV bytecode reading** (`rev_19-yarv-whisperer.md`):
      `RubyVM::InstructionSequence.load_from_binary(Base64.decode(BLOB))` + `.disasm`; pull constants
      from the ISeq array.
- [ ] **Kernel/eBPF oracle = static section read** (`rev_21-kernel-oracle.md`): treat `.bpf.o` as an
      ELF, dump `.rodata`; never load it.
- [ ] **Self-checksum + GF(2) linear system** (`rev_17-linear-descent.md`): replicate
      `sum(section)&0xFF` to decrypt instead of patching; solve `M*x=T` by Gaussian elimination.
- [ ] **Esoteric-runtime transliteration** (`rev_22-threaded.md`): Forth/RPN (and similar) verifiers
      just re-encode the simple byte relation — read tables from source, don't execute.

OSINT
- [ ] Reverse image search + EXIF geolocation; username enumeration; Wayback/archive; DNS/WHOIS/CT;
      Shodan/Censys; document metadata. (Click2Trace-specific OSINT writeups pending — source 403.)
