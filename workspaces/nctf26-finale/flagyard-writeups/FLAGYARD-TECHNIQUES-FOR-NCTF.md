# FlagYard (Black Hat MEA) Technique Digest — for the NCTF26 Finale

Compiled 2026-11-13 from the sources listed in `SOURCES.md`. Every claim below cites the exact
local file, repo path, or gist it came from. All downloaded code was **read only, never executed**.

## Retrieval status

| Source | Where it landed | Status |
|---|---|---|
| A1 hokan solver | `downloads/hokan/hokan_solver.py` | read OK (pre-existing local) |
| A2 baby_pwn solver | `downloads/baby_pwn/Baby_Pwn_Solver.py` | read OK (pre-existing local) |
| B1 z0v3r1n/ctf-scripts | `downloads/z0v3r1n-ctf-scripts/flagyard/` | **cloned OK — 15 challenge solvers** |
| B2 Polymero Whack-A-Scratch gist | `downloads/polymero-whack-a-scratch/gist_fetch.txt` | fetched, but gist is only a **solve-log transcript**, not source (see caveat) |
| B3 7Rocky SaqrSign gist | `downloads/7rocky-saqrsign/gist_fetch.txt` | fetched OK — **full Sage solver source** |
| B4 Jorian Woltjer PRNG book | WebFetch | summarized OK |
| B4 cor.team twist_and_shout | WebFetch | summarized OK |
| B4 imp.ress.me seccon janken | WebFetch | summarized OK |
| B5 YouTube `6FGPY5Ips8Y` | — | **noted only, not downloaded** (per instructions) |

**Total: 6 of 6 fetchable sources retrieved; 0 failed.** One caveat: the Polymero gist (B2) is the
*program's stdout transcript*, not the `solver.py` source, so the Whack-A-Scratch technique below is
reconstructed from the log plus the inline Discord note in `SOURCES.md` §C — flagged where uncertain.

---

## CRYPTO

### SaqrSign — statistical side-channel key recovery on a lattice/NTT signature scheme
- **Source:** `downloads/7rocky-saqrsign/gist_fetch.txt` (full Sage source). Cross-ref `SOURCES.md` §C "saqrsign".
- **Mechanism:** A Falcon/Dilithium-style signature over the ring `Z_Q[x]/(x^N+1)` with `N=1024, Q=12289`,
  NTT domain `NTTDomain(Q, W=4324, P=9389)`. Each signature exposes masked polynomials `V,W` plus a
  challenge `c = HashBall(m||r, tau=38)` — a deterministic **sparse** polynomial of fixed Hamming weight 38.
  Because `c` is sparse and the per-signature mask is zero-mean, the signatures leak a biased statistic.
- **Exploit:** Collect `num_sigs=300` signatures. For each, undo the NTT (`INTT`) and the per-coefficient
  twist `pow(P,-i,Q)` to recover centered `z,w` polynomials, then accumulate a **correlation trace**
  `trace_g[j] += c0 * z[idx]` over every nonzero challenge coefficient (the classic "average out the mask"
  attack). Divide by the trace count, renormalize by `sqrt(2N/(3*sq_norm))`, round to integers to get the
  secret `pred_g`, then **forge** the public relation `d = E*g - A` and submit `d` as the forgery to the
  remote (menu `c`, `> (hex)`).
- **Reusable for NCTF:** If a lattice-signature challenge gives you *many* signatures and a *sparse* hashed
  challenge, think **statistical averaging to recover the secret key**, not a single-signature lattice CVP.
  The `HashBall` sparse-poly generator and `INTT`+centered-lift helpers in this gist are directly adaptable.
  Needs SageMath + a local `ntt.py` (`NTTDomain`) — have Sage ready.

### Whack-A-Scratch — Legendre-symbol oracle key recovery (BHMEA 2025 quals)
- **Source:** `downloads/polymero-whack-a-scratch/gist_fetch.txt` (solve-log only) + `SOURCES.md` §D.
- **Mechanism (reconstructed from the log — treat as approximate):** The challenge builds key matrices whose
  secret entries are probed through a **Legendre-symbol oracle**. The solver pre-generates a "Legendre
  sequence dictionary", then "whacks until the determinant Legendres of the key matrices are all unity"
  (forces the matrices into a solvable/invertible regime), and recovers each diagonal entry `[loop][i][i]`
  by matching observed Legendre sequences against the dictionary (~250–340 oracle calls per entry).
- **Exploit shape:** Offline dictionary of Legendre sequences → online oracle (≈3400 calls, ~1 hr) → narrow
  each key coordinate to 1–2 candidates → brute-force the ~2^k combined key → AES/stream decrypt the flag
  (`BHFlagY{D3BUGG1NG_1S_FUN}`).
- **Reusable for NCTF:** Recognize **quadratic-residue / Legendre-symbol oracles** as key-recovery side
  channels. Pattern = precompute QR-sequence lookup table offline, spend oracle budget online.
  *Caveat: we only have the transcript; the actual algorithm details are inferred.*

### hokan — final-stage OpenSSL blob: PBKDF2-HMAC-SHA256 → AES-256-CBC
- **Source:** `downloads/hokan/hokan_solver.py` lines 134–150. (Full chain also under FORENSICS below.)
- **Mechanism:** The recovered file `flag.txt.enc` is an OpenSSL `Salted__` blob. Parameters recovered from
  the captured command: **AES-256-CBC, PBKDF2-HMAC-SHA256, 200000 iterations, 8-byte salt** (bytes `[8:16]`).
- **Exploit:** `pbkdf2_hmac('sha256', password, salt, 200000, dklen=48)` → `key=material[:32]`, `iv=material[32:48]`
  → AES-CBC decrypt → strip PKCS#7 → regex `BHFlagY\{...\}`.
- **Reusable for NCTF:** The canonical `openssl enc -aes-256-cbc -pbkdf2 -iter 200000` layout. Keep this
  exact 5-line decrypt snippet (salt at offset 8, dklen=48 to carry key+IV) in the toolkit.

### PRNG / Mersenne-Twister recovery reference set (for GachaFlag-class crypto)
- **Source:** WebFetch summaries of B4 (`book.jorianwoltjer.com`, `cor.team/.../twist_and_shout`,
  `imp.ress.me/.../janken-vs-kurenaif`). No local file.
- **Mechanisms & tooling (Python `random` = MT19937):**
  - **Full 32-bit outputs:** feed 624 outputs to `mt19937predictor.setrandbits()` → exact future prediction.
    Wider outputs (multiples of 32, e.g. 512-bit) need proportionally fewer samples (~20,000 state bits total).
    `randcrack` does the same.
  - **Predict the past:** `untwist()` reverses the twist to step the state back 624 at a time; `offset(n)`
    realigns to values generated *before* a leak.
  - **Truncated / partial outputs:** `symbolic_mersenne_cracker` (icemonster `Untwister`) builds the temper +
    twist as **Z3 bit-vector constraints** over the 19937-bit state, takes binary strings with `?` for unknown
    bits, `solver.check()`, returns a synced `random`. Works with e.g. 16 bits × ~1337 samples. Slower but
    handles the hard cases.
  - **twist_and_shout pattern:** invert tempering per word; reverse `MT[i]=MT[i+m]^xA` by computing
    `xA=MT[i]^MT[i+m]` on already-twisted indices (227..623 for m=397), branch on the low bit for the two
    `x` candidates, then **prune with a printable-ASCII oracle** when the flag sits contiguously in state.
  - **janken/kurenaif pattern (invert the *seed*):** constrain desired outputs (each `randint(0,2)` fixes the
    top 2 bits of one MT word), symbolically solve for the **post-seed** state (fix index=624, first word
    `0x80000000`), then reimplement CPython `init_by_array` in Z3 with 624 unknown key words and solve for a
    single integer seed that the server will accept.
  - **Other PRNGs:** PHP `mt_rand` → `php_mt_seed` (2^32 brute); V8 `Math.random` (xorshift128+) → ~5 raw /
    ~15 floored outputs via Z3 (`v8_rand_buster`); Java LCG (48-bit) → few samples, LLL for truncated
    (`truncated_java_random.py`, Sage); Bash `$RANDOM` → brute 2–3 samples.
- **Reusable for NCTF:** Decision tree = *full outputs?* → `mt19937predictor`/`randcrack`. *Truncated/partial?*
  → `symbolic_mersenne_cracker` (Z3). *Need a seed the server accepts?* → symbolic `init_by_array` inversion.
  Pre-stage all three libs offline.

---

## PWN

All 15 FlagYard pwn solvers live under `downloads/z0v3r1n-ctf-scripts/flagyard/<chall>/`. Grouped by technique.

### Stack / variable-overwrite primitives
- **babyauth** (`babyauth/xpl.py`, `babyauth/main.c`): `getval()` reads with `scanf("%ld")` into a pointer to
  an **`int`** (`(long*)&len`). Sending `4294967328` = `0x1_00000020` writes 8 bytes: low dword `0x20` into
  `len`, high dword `1` into the **adjacent `is_admin`** stack slot → auth bypass → `system("/bin/sh")` with
  no real password. *Pattern: `%ld`-into-`int` type confusion clobbering a neighbor flag.*
- **byte** (`byte/solution.py`): 32-bit classic stack overflow — `p32(0x080491e0)*34` sprays the win-function
  address across saved EIP (ret2win, no leak needed).
- **lucky** (`lucky/xpl.py`): leak libc via a printed "ID" (`- 0x1eb380`), then an **out-of-bounds array index**
  (menu "change index 18") writes a ROP chain onto the stack: `ret` alignment gadget + `pop r12` + one-gadget
  `libc+0xe6c7e`. *Pattern: OOB index as arbitrary stack write.*
- **reader** (`reader/solution.py`): path-traversal-ish file reader that also has a stack overflow. Leaks PIE
  and libc straight from `/proc/self/maps` (reads `r-x`/`r--` base lines), then overflows with
  `"flag"+padding` + a PIE return + `pop rdi; ret` + `/bin/sh` + `system`. *Pattern: `/proc/self/maps` as a
  free ASLR defeat when the bug is an arbitrary file read.*

### Heap: tcache poisoning & safe-linking
- **heap-yard** (`heap-yard/xpl.py`): glibc 2.39 UAF. Defeats **tcache safe-linking** with
  `write(0, p64(ptr ^ view(1)))` (the leaked fd *is* the mangled next-ptr, XOR to forge), redirects a chunk
  onto `got['free']`, leaks libc via `view`, overwrites `got.read`/`free` and drops a one-gadget `0xef52b`.
- **nametagv2** (`nametagv2/xpl.py`): tcache dup/poison on 0xe0 chunks → point a chunk at `__free_hook`,
  write `system`, write `/bin/sh` into another chunk, `free` it → shell. Libc leak via unsorted-bin pointer
  in a freed 0x500 chunk (`- 0x3ebca0`, glibc 2.27-era `__free_hook` path).
- **nametag** (`nametag/xpl.py`): double-free → overlap; edits a freed chunk's fd to `leaked-160-0x10` to
  reallocate over a target and `show` it (info leak / arbitrary read variant).
- **fs** (`fs/xpl.py`): tcache poisoning chain — leak libc from unsorted bin (`view(0)-0x3b5d70`), leak heap,
  forge fd into `stdin`/stack, then write a `ret2system` chain (`pop rdi` `0x21852`, ret `0x17d22e`, `system`).
- **phone-book** (`phone-book/solve.py`): glibc 2.27 **House-of-Force-style** top-chunk abuse — overwrite the
  top chunk size with `0xffffffffffffffff` via an oversized name, compute `distance` to `__malloc_hook-0x40`,
  `malloc` that huge size to move top, then write `system` over `__malloc_hook` and trigger with
  `malloc(binsh)` (size field carries the `/bin/sh` pointer). Libc leak via negative index `leak(-6)`.

### FILE-structure exploitation
- **logger** (`logger/xpl.py`): forges `_IO_FILE` via pwntools `FileStructure()`. Uses `0xfbad2c80` flags +
  crafted `_IO_file_jumps` to leak heap+libc, then `FileStructure().read()/write()` for **arbitrary
  read/write** of `environ` (stack leak) and finally writes a `system("/bin/sh")` ROP onto the stack.
- **baby_pwn** (`downloads/baby_pwn/Baby_Pwn_Solver.py`, 937 lines — the single most reusable template):
  a menu with a `poke(arr[idx]=val)` + "fire" (calls whatever `memset@GOT` points to) primitive. Full chain:
  1. **Neutralize the canary** by pointing `__stack_chk_fail@GOT` at the main loop (`B.got_chk = B.main_loop`)
     so a canary failure *loops* instead of aborting.
  2. **Forge an `_IO_2_1_stdout_` object** (`p64(0xFBAD1800)` + read/write pointers) to leak the GOT/FILE
     region; recover libc base from `atol` (`atol_addr - L_OFF.atol`), with a strict `stdout` offset sanity
     check against the remote libc.
  3. Leak `__environ` → find the saved RIP slot of `main` by scanning a 0x1000 stack window for a value in
     `[__libc_start_call_main .. +1]`.
  4. Write an **open/getdents64/read/write ORW ROP** (`rop_call()` builds `pop rdi/rsi` + `pop rbx;mov rdx,rbx`
     for the 3rd arg) to `open("/")`, dump the directory, read the flag filename interactively, open+read+write it.
  - *This file is a reusable library:* `rop_call(libc, fn, rdi, rsi, rdx)`, `token()` (decimal-ascii input),
    forged-FILE leak/write, and canary-GOT-redirect are all drop-in.

### Shellcode / syscall-only (seccomp-muted) & SROP
- **muted_shell** / **muted_shellv2** (`muted_shell/exploit.py`, `muted_shellv2/xpl.py`): execve is
  seccomp-blocked but the **flag is pre-opened as fd 3**. Hand-rolled **ORW shellcode**: `read(3, rsp, 0x80)`
  then `write(1, rsp, rax)`. v2 ships the exact 26 opcode bytes (`\x31\xc0\x6a\x03\x5f\x54\x5e...`). *Pattern:
  "muted"/no-execve ⇒ read an already-open fd, don't spawn a shell.*
- **trinity** (`trinity/xpl.py`): tiny stager — send `\x5a\x0f\x05` (`pop rdx; syscall`) padded, then a second
  read delivers `shellcraft.sh()`. *Pattern: 3-byte `pop rdx;syscall` self-bootstrapping read.*
- **soleOfRop** (`soleOfRop/solution.py`): static binary, **SROP**. `SigreturnFrame` with `rax=59` (execve),
  `rdi=0x6001aa` (a "/bin/sh" in .data), `rip=syscall gadget 0x4000fd`; the stack sets `rax=0xf` (sigreturn)
  via a `pop rax;...` at `0x400177` then the syscall. *Pattern: no libc, few gadgets ⇒ SROP via one
  `syscall;ret` + a way to set `rax=15`.*
- **shell_land** (`shell_land/xpl.py`): just replays a precompiled `payload.bin` (shellcode, contents opaque).

### Reusable-for-NCTF pwn takeaways
- Have the **baby_pwn library** (`rop_call`, forged-FILE leak, canary-GOT-redirect, ORW chain) ready — it
  covers "write-what-where menu → full remote ORW" end to end.
- Keep one-gadget offsets handy and the **safe-linking XOR-unmangle** one-liner for glibc ≥ 2.32 tcache.
- `/proc/self/maps` (reader) and unsorted-bin/`atol` leaks are your default ASLR defeats.
- seccomp challenge ⇒ ORW shellcode on **fd 3**; static/no-libc ⇒ SROP.

---

## REVERSE

No reverse *solver scripts* were in the fetched sources; the following are Discord inline notes
(`SOURCES.md` §C) mapped to the right tooling. Treat as technique pointers, not verified code.

### Breakout — z3 over a single linear sum constraint
- **Source:** `SOURCES.md` §C (Chiira). **Mechanism:** ~50 `qword_*` arrays of 8-bit values combined into one
  linear equation `total_sum == 0x1BADCF514706D`. **Exploit:** declare each flag char as a z3 `BitVec(8)`,
  encode the single linear constraint, add printable-range constraints, `solve`. *Reusable: whenever a
  keygen reduces to one (or few) linear equations over flag bytes, z3 is instant.*

### zigger — invertible per-char XOR transform
- **Source:** `SOURCES.md` §C (Yuns). **Mechanism:** linear XOR transform `decoded = f(encoded[i], i, k)`.
  **Exploit:** either algebraically invert per-char, or express `decoded[i]` symbolically in z3 in terms of
  `encoded[i]`, `i`, `k` and solve. *Reusable: linear/XOR checks are directly invertible — don't brute.*

### Dev3il general note — CFG flattening ⇒ prefer angr
- **Source:** `SOURCES.md` §C (Dev3il). **Mechanism:** IDA pseudocode obscured by **control-flow flattening**
  (a dispatcher `while(state){switch(state)}`). **Exploit:** symbolic execution with **angr** instead of
  hand-reversing the flattened dispatcher; constrain stdout == "correct" and `explore(find=...)`. Note: z3
  alone can yield *many* valid flags (one part had 260) — add structural constraints (printable, known prefix
  `BHFlagY{`/`NCTF{`) to disambiguate. *Reusable: flattening/VM obfuscation ⇒ reach for angr + CFG recovery.*

### Reusable-for-NCTF reverse takeaways
- First triage: does the check reduce to **linear/XOR constraints**? → z3 BitVec (Breakout, zigger).
- Is it **obfuscated/flattened/virtualized**? → angr symbolic solve (Dev3il). Always pin the flag format as a
  constraint to collapse spurious solutions.

---

## FORENSICS

### hokan — pcap → gRPC/protobuf over HTTP/2 → AES-GCM → OpenSSL blob (full multi-stage chain)
- **Source:** `downloads/hokan/hokan_solver.py` (complete, 156 lines). The single richest forensics template here.
- **Mechanism / the chain, stage by stage:**
  1. **PcapNG parse (scapy):** `PcapNgReader`, keep only TCP on **port 50051** (gRPC default). Bucket payloads
     per TCP flow keyed by `tcp.seq`.
  2. **TCP reassembly:** `reassemble()` sorts by seq and handles overlaps/retransmits to rebuild each stream.
  3. **HTTP/2 framing (hand-rolled):** skip the `PRI * HTTP/2.0` 24-byte preface, walk 9-byte frame headers
     (`length[3] | type[1] | flags[1] | streamid[4]`), collect DATA frames (`kind==0`) per stream id, strip
     padding when the PADDED flag (`flags & 8`) is set.
  4. **gRPC length-prefixed messages:** each is `compressed[1] | length[4] | protobuf`.
  5. **Protobuf decode (hand-rolled):** `varint()` + wire types 0 (varint) and 2 (length-delimited) → field map.
  6. **AES-GCM decrypt:** a recovered 32-byte `SESSION_KEY`; each message carries a **12-byte nonce** (field 1
     client→server, field 3 server→client) + ciphertext; `AESGCM.decrypt(nonce, ct, None)`, then re-parse the
     plaintext as protobuf. Pull the `key.txt` write (field 4 ends with `key.txt`, field 5 = password) and the
     `Salted__` OpenSSL download (field 4).
  7. **Final OpenSSL decrypt:** PBKDF2-HMAC-SHA256 / 200k / AES-256-CBC (see CRYPTO above) → `BHFlagY{...}`.
- **Reusable for NCTF:** This is a **complete gRPC-pcap extractor** that needs no external protobuf schema —
  it decodes HTTP/2 DATA frames and protobuf wire format by hand. If a forensics challenge gives you a pcap
  with TLS-free gRPC/HTTP2 (port 50051 or any `h2c`), lift `grpc_messages()` + `protobuf()` + `varint()`
  wholesale. Keep scapy + `cryptography` staged. The AEAD-then-nested-protobuf pattern (decrypt reveals *more*
  protobuf) is common — always re-parse plaintext.

---

## WEB

No web-specific solver appeared in the fetched sources. The z0v3r1n repo's FlagYard folder is **pwn-only**
(verified: `find flagyard -name '*.py'` lists only pwn exploits + one `main.c`). `SOURCES.md` §B claimed the
repo had "pwn + web" solvers, but **no web scripts are present** — stated explicitly rather than guessed.
For web in the finale, rely on the repo's existing `web-triage`/`ctf-web` skills; nothing new is added here.

---

## Toolkit checklist (stage these before the finale)

Concrete, reusable artifacts worth having ready, with the source that demonstrates each:

- [ ] **z3 BitVec linear-constraint template** — one `BitVec(8)` per flag byte + printable range + the keygen's
      linear/sum/XOR equation + format prefix. Demonstrated conceptually by Breakout & zigger (`SOURCES.md` §C).
- [ ] **Mersenne Twister toolkit (3 tiers):** `mt19937predictor`/`randcrack` (full 32-bit outputs),
      `symbolic_mersenne_cracker` Z3 `Untwister` (truncated/partial bits), and a **Z3 `init_by_array` seed
      inverter** (force a server-accepted seed). Ref: B4 blog summaries. Pre-`pip`-install offline.
- [ ] **gRPC/HTTP2-over-pcap extractor** — `varint()`, `protobuf()`, `grpc_messages()` (HTTP/2 frame walker +
      DATA reassembly) from `downloads/hokan/hokan_solver.py`. Scapy + `cryptography`.
- [ ] **OpenSSL `Salted__` decrypt snippet** — PBKDF2-HMAC-SHA256/200k/AES-256-CBC, salt at `[8:16]`,
      `dklen=48` (key+IV). From `hokan_solver.py:134-150`.
- [ ] **Lattice/NTT signature statistical forgery (Sage)** — `HashBall` sparse-poly, `INTT` + centered-lift,
      correlation-trace averaging over 300 sigs, `E*g - A` forgery. From `downloads/7rocky-saqrsign/gist_fetch.txt`.
      Needs SageMath + the challenge's `ntt.py`.
- [ ] **angr symbolic-solve skeleton** — `proj.factory.simgr(state); simgr.explore(find=success_addr,
      avoid=fail_addr)`; use for CFG-flattened/VM reverse (Dev3il note). Always add flag-format constraints.
- [ ] **baby_pwn exploit library** (`downloads/baby_pwn/Baby_Pwn_Solver.py`) — `rop_call(libc,fn,rdi,rsi,rdx)`,
      forged-`_IO_2_1_stdout_` leak/arb-write, **canary-neutralize via `__stack_chk_fail@GOT → main_loop`**,
      saved-RIP finder (scan stack for `__libc_start_call_main`), and the open/getdents64/read/write ORW chain.
- [ ] **Heap primitives:** tcache **safe-linking unmangle** (`fd ^ (heap>>12)`; see heap-yard
      `ptr ^ view(1)`), `__free_hook`/`__malloc_hook` overwrite (nametagv2, phone-book), FILE-struct arb R/W
      via pwntools `FileStructure()` + `0xFBAD` flags (logger). Repo: `flagyard/{heap-yard,nametagv2,phone-book,logger}`.
- [ ] **Shellcode kit:** ORW-on-fd-3 for seccomp-muted targets (muted_shell/v2), 3-byte `pop rdx;syscall`
      stager (trinity), and **SROP** `SigreturnFrame(rax=59)` for static/no-libc (soleOfRop).
- [ ] **ASLR defeats:** `/proc/self/maps` read (reader), unsorted-bin libc leak, and `atol`/known-symbol GOT
      leak → libc base with an offset sanity check (baby_pwn).
- [ ] **PRNG decision reflex:** full outputs → predictor lib; truncated → Z3 untwister; need a seed → Z3
      `init_by_array`; non-Python → `php_mt_seed` / `v8_rand_buster` / Java-LLL / `BashRandomCracker`.

**Note:** YouTube `youtu.be/6FGPY5Ips8Y` (pwn walkthrough) was **not** downloaded, per instructions — review
manually if a live pwn needs it.
