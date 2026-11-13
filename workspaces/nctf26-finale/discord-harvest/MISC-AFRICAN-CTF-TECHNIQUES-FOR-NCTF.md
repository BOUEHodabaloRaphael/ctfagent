# African / Francophone CTF Technique Digest — NCTF Finale Prep

**Built:** 2026-11-13
**Scope:** Technique digest mined from 6 cloned writeup repos + 3 WebFetch'd blog posts, all from the same African/francophone CTF scene as the NCTF finale (HackerLab Bénin, 404CTF, 0xfun, kBxAc, NICCTF).
**Security:** Everything under `downloads/misc/` is UNTRUSTED CTF code. This digest was produced by READING only — nothing was executed, built, or installed.

> How to read this: the single richest source is **Heviosso HackerLab2023** (a full francophone African CTF with real solutions across all 7 categories) — it is the best predictor of NCTF beginner→mid difficulty. **404CTF-2026** (official French, HackademINT) predicts the higher-end + "realistic" style. The **achbelsdn HackerLab-2026** repo is a **catalog of challenge statements only** (every solution is "À compléter") but it reveals the 2026 HackerLab Bénin challenge taxonomy/theme, which is directly on-scene for NCTF.

---

## Source inventory (cloned vs fetched vs failed)

| Source | Path / URL | Status | Value |
|---|---|---|---|
| Heviosso/Writeup (HackerLab2023) | `downloads/misc/Heviosso-Writeup/HackerLab2023/` | CLONED ✅ (73 writeups, all categories) | **HIGHEST** — full solutions, same scene |
| HackademINT/404CTF-2026 (official sources) | `downloads/misc/HackademINT-404CTF-2026/` | CLONED ✅ (82 MB, shallow) | Challenge **sources** (no solutions); category taxonomy |
| AnouarVision/ctf-writeups | `downloads/misc/AnouarVision-ctf-writeups/` | CLONED ✅ | 404CTF-2026 + StarHackademINT-2026 **solved** writeups (EN+IT) |
| paveledits/Writeups (0xfun 2026) | `downloads/misc/paveledits-Writeups/0xfun CTF 2026/` | CLONED ✅ | Only `crypto-baby_HAWK` under 0xfun; rest of repo = other CTFs |
| Jazzruran/writeups (kBxAc 2026) | `downloads/misc/Jazzruran-writeups/CTFs/kBxAc 2026/` | CLONED ✅ | 1 deep pwn writeup (`lets_get_to_library`) + PwnSec/HTB |
| achbelsdn/Hackerlab-2026-quals | `downloads/misc/achbelsdn-Hackerlab-2026-quals/` | CLONED ✅ | **Catalog only** — statements, no solutions |
| kore.one shell writeup | https://kore.one/0xfun-ctf-2026-shell-challenge-writeup/ | FETCHED ✅ | ExifTool CVE-2021-22204 RCE |
| ghostinthefingers six-seven-lmao | https://ghostinthefingers.github.io/posts/six-seven-lmao/ | FETCHED ✅ | glibc 2.42 heap UAF |
| ghostinthefingers six-seven-revenge | https://ghostinthefingers.github.io/posts/six-seven-revenge/ | FETCHED ✅ | glibc 2.42 off-by-one / House of Einherjar |
| NICCTF-2026 Notion | notion.so/NICCTF-2026-Writeups-... | **UNFETCHABLE ⚠️** | JS-only / blocked — 307-redirects to app.notion.com, renders only "Notion" title with no content. Needs a headless browser to read. |

---

## PWN / Binary Exploitation

### ret2gets libc leak (no gadgets in binary) — **kBxAc 2026**
- **Repo:** `Jazzruran-writeups/CTFs/kBxAc 2026/lets_get_to_library/writeup.md`
- **Mechanism:** Classic `gets()` stack overflow (buf `0x80`, NX + Partial RELRO, zero useful ROP gadgets in the binary, static `printf` instead of `puts`). The binary is driven as a call-oriented chain: calling `gets` leaves the libc `_IO_stdfile_0_lock` pointer in `rdi` as a side effect; a second `gets` writes `%p` into that lock; then `printf` is called with the format in place to leak a libc pointer from `rsi` (points inside `_IO_2_1_stdin_`).
- **Exploit + tools:** pwntools, Binary Ninja (gadget search plugin), gdb/gef, `pwninit`. Carefully size the lock-write payload to 5–7 bytes so the subsequent `gets` unlock routine (`_IO_lock_unlock`) doesn't clear `owner`/`lock` and deadlock. After the leak, return to `main` for a second overflow and a 3-gadget libc ROP: `pop rdi; "/bin/sh"; system`.
- **Reusable for NCTF finale:** When a pwn binary has **no gadgets and uses `printf` on a static string**, suspect an intentional leak primitive. Register side-effects of libc functions (`gets`→`rdi`=stdin lock, scratch regs not preserved across calls) are a reliable leak path. Keep `ret2gets`/`ret2printf` in the toolbox for stripped, gadget-poor binaries.

### glibc 2.42 heap UAF → ROP (six-seven) — **0xfun-scene blog**
- **Source:** https://ghostinthefingers.github.io/posts/six-seven-lmao/
- **Mechanism:** `delete_note` frees a chunk but leaves the dangling pointer + size → use-after-free giving read/write primitives. Leak libc via unsorted-bin `main_arena` ptr; leak heap base via a safe-linked tcache `fd` (`>>12`); poison tcache toward `environ-24` for a stack leak; poison again toward saved RIP for a ROP chain (`ret; pop rdi; "/bin/sh"; system`).
- **Tools:** pwntools (ELF/ROP), gdb, provided patched libc.
- **Reusable:** Tcache **safe-linking** only needs a heap-address leak to defeat (`key = addr>>12`). `environ` reliably yields a stack address. Keep fake chunks 0x10-aligned and avoid the tcache `key` field.

### glibc 2.42 off-by-one → House of Einherjar (six-seven-revenge) — **0xfun-scene blog**
- **Source:** https://ghostinthefingers.github.io/posts/six-seven-revenge/
- **Mechanism:** 1-byte null overflow in `edit_note` clears the next chunk's PREV_INUSE → House of Einherjar backward-consolidation → overlapping chunks → tcache poisoning → ORW syscall chain (because `system` is seccomp-filtered).
- **Reusable:** A single null byte on allocator metadata is enough for full control. When `system` is blocked by **seccomp**, fall back to an `open/read/write` syscall ROP to print `flag.txt`.

### Shared-object / `.so` function hijack for SUID privesc — **HackerLab2023**
- **Repo:** `Heviosso-Writeup/HackerLab2023/PWN/Dark_HackerLab.md`
- **Mechanism:** SSH access to a box with a SUID binary (`so-shared`, SUID `scort`) that `ldd` shows links `libhackerlab.so` and calls a `beautify()` function. The library is writable/overridable.
- **Exploit + tools:** `ldd`, `strings`, `readelf`. Compile a malicious `beautify()` that does `setuid(0); system("/bin/bash -p")`, build it with `gcc -shared -fPIC -o libhackerlab.so`, place it where the SUID binary loads it, trigger via the menu → shell as the file owner.
- **Reusable for NCTF finale:** For SUID/boot2root privesc, **check `ldd` for writable/relative shared libraries** and library-path hijacking before anything else. HackerLab Bénin loves SUID + shared-object tricks.

### Win-function / leak + offset buffer overflow — **HackerLab2023**
- **Repos:** `PWN/Warmup1.md` (blind 77-byte overflow to a win function), `PWN/Warmup3.md` (program prints `str_head` address; `binsh` var is at a fixed `+0x10` offset; feed `str_head+0x10` to hit the `system(binsh)` branch).
- **Tools:** gdb (breakpoint on `vuln`, disassemble to find the `lea` offset), ghidra.
- **Reusable:** Many African-CTF "warmup" pwns are **no-PIE, leak-one-address-then-add-a-static-offset**. Always check whether the binary prints any address you can pivot from.

### Linux kernel pwn: alphanumeric shellcode + kernel-module arbitrary write → privesc — **PwnSec 2026 (same author scene)**
- **Repo:** `Jazzruran-writeups/CTFs/PwnSec CTF 2026/death_ops/writeup.md`
- **Mechanism:** Two-stage. Stage 1: userland `blackops` binary (canary/NX) constrained to **alphanumeric shellcode**. Stage 2: vulnerable `shadowops.ko` kernel module gives a constrained arbitrary write used to **strip seccomp** and overwrite `task_struct` creds for root. QEMU with `kASLR` + `kPTI` + KVM, initramfs/`bzImage`/`rootfs.cpio.gz`.
- **Tools:** QEMU, `cpio`/`zcat` to unpack initramfs, Binary Ninja, gef.
- **Reusable for NCTF finale:** If the finale has a `bzImage`+`rootfs.cpio.gz`+`run-qemu.sh` bundle, it's kernel pwn — unpack initramfs first (`zcat … | cpio -idmv`), read `/init` for the flag path + module load, note kASLR/kPTI/SMEP/SMAP in the `-append` line. task_struct cred overwrite remains the standard privesc.

### 404CTF-2026 official pwn surface (sources only, predicts style)
- **Repo:** `HackademINT-404CTF-2026/ExploitationDeBinaires/` — 9 challenges: `Jeu-de-la-Heap` (heap), `sophie-gerlibcstartmain` (ret2libc/`__libc_start_main`), `frais-net` (net service), `fascinants-travaux-de-galois`, `la-bonne-recette`/`le-bon-ingredient`/`le-bon-instrument` (series), `notes-pour-rene-thom`, `Creneau-serre`.
- **Reusable:** Expect heap + ret2libc + format-string families at the top end. (Sources present; no official solutions in-repo.)

---

## Web

### SSTI (Flask/Jinja2) RCE — **HackerLab2023**
- **Repo:** `Heviosso-Writeup/HackerLab2023/Web/Les tresors.md`
- **Mechanism:** Flask app reflects a `submit=` param; `{{7*7}}` → `49` confirms Jinja2 SSTI.
- **Exploit:** `{{ self.__init__.__globals__.__builtins__.__import__('os').popen('cat /flag.txt').read() }}` (PayloadsAllTheThings). Tools: Burp.
- **Reusable:** First web RCE probe should be `{{7*7}}` / `${7*7}`. Flask is extremely common on this scene.

### XXE file read — **HackerLab2023**
- **Repo:** `Web/MESSAGE.md`. `robots.txt` leaks a `[message]` param; POST body param name is `xml` → classic XXE. `<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///var/www/flag.txt">]>`. Tool: Burp.
- **Reusable:** Any XML-consuming endpoint → try `SYSTEM "file:///etc/passwd"` then walk to `/var/www/flag.txt`. Read `robots.txt` for hidden param names.

### SQLi → sqlmap, and manual blind UNION SQLi via a Discord bot — **HackerLab2023**
- **Repos:** `Web/FAKE_POWER.md` (POST `info` param, `sqlmap -r req -p info --dbs/--tables/--dump`), `Misc/Hacker Bot.md` (blind SQLi through a Discord bot `!auth`).
- **Mechanism (bot):** Filters block spaces (bypass by quoting the whole payload `"..."`) and lowercase `or` (bypass with `OR`). Then `LIMIT/OFFSET`, `UNION SELECT`, `INFORMATION_SCHEMA.SCHEMATA/TABLES/COLUMNS` to map multiple `flagX` DBs, and `LOAD_FILE(0x2e666c...)` (hex-encode the filename to beat a name filter) reading from `@@secure_file_priv` = `/var/lib/mysql-files/`.
- **Reusable for NCTF finale:** SQLi shows up **inside chat bots**, not just web forms. Keyword/space filters are beaten by quoting, case-swap (`OR`), and **hex-encoding file paths**. Remember `LOAD_FILE` + `@@secure_file_priv` to read server files via MySQL.

### JWT weak-secret crack → IDOR brute — **HackerLab2023**
- **Repos:** `Web/DIN.md`, `Web/Prize Hunter.md`
- **Mechanism:** App signs JWTs (HS256) with a weak secret (`breakingfree`). Crack with **john** on the token; re-sign with Burp **JWT Editor**; iterate an in-token id (`picture_id` / `sub`) → IDOR. DIN brute-forces 5000 tokens through Burp Intruder; flag at a specific id.
- **Reusable:** Every JWT → immediately `john`/`hashcat` the HS256 secret. The id-inside-JWT is usually an IDOR once you can re-sign.

### IDOR (naive) + cookie tampering + unicode steg in HTML — **HackerLab2023**
- **Repos:** `Web/Baby-hunter1:rodi.md` (`/user?id=0`), `Web/Baby-hunter: cookies.md` (change cookie `name=visitor`→`admin`; admin page hides the flag in **zero-width unicode** decoded via `330k.github.io/misc_tools/unicode_steganography.html`).
- **Reusable:** Try `id=0` / negative ids first. Cookie role values (`visitor`/`user`→`admin`) are a constant. Invisible/zero-width unicode in page source is a recurring flag hiding spot.

### Node.js `fs.readFileSync` URL-object type-juggling LFI (filter bypass) — **HackerLab2023**
- **Repo:** `Web/Bazik node.md`
- **Mechanism:** Express app reads a `file` GET param; middleware blocks the string `flag`. `fs.readFileSync` accepts a **URL object**; Express parses `file[k]=v` into an object. Craft a fake URL object and double-URL-encode the name: `file[origin]=x&file[href]=x&file[protocol]=file:&file[hostname]=&file[pathname]=fla%2567.txt`.
- **Reusable:** Node LFI filters are bypassed by **parameter-to-object type juggling** (`a[b]=c`) and layered URL-encoding (`%2567`→`%67`→`g`). Know which sink functions accept non-string types.

### VM/sandbox escape (`vm`/`vm2`) — **HackerLab2023**
- **Repo:** `Web/Renderer 2.md`
- **Mechanism:** Input runs in Node `vm.runInNewContext(...Object.create(null))`; escape via `new Proxy({},{get:function(me,key){(arguments.callee.caller.constructor('console.log(SECRET)'))()}})` reaching the outer `Function` constructor → read `process.env.FLAG`.
- **Reusable:** Node `vm`/`vm2` sandboxes are escapable via `arguments.callee.caller.constructor` / Proxy-get tricks (jcreedcmu gist). Flag usually in `process.env`.

### URL-parse confusion → stored XSS / SSRF — **HackerLab2023**
- **Repos:** `Web/Renderer 1.md` (tool prefixes `https://hackerlab.bj` then appends `.js`; bypass with `@attacker.com/script` so the host becomes attacker-controlled; exfil admin cookie via ngrok JS), `Web/Sn4p-Sh0t.md` (SSRF screenshot app; filters block `file://`/`127.0.0.1`; bypass `File:///http/../../flag.txt`).
- **Reusable:** URL-format/parser confusion (`@host`, scheme-case, `../` traversal in `file:` URIs) is the dominant SSRF/XSS bypass family. Keep HackTricks "URL format bypass" + the `@attacker.com` trick handy; use ngrok for OOB cookie exfil against admin bots.

### HTTP header / method auth bypass — **HackerLab2023**
- **Repos:** `Web/Connect you.md` (chain `REQUEST_METHOD`→POST, `X-Forwarded-For: 127.0.0.1`, `User-Agent: admin`, then `username=admin&password=admin`), `Web/Refff.md` (nginx needs `Referer: https://hackerlab.bj` but app needs `Referer: FLAG{...}` → send the **Referer header twice** with two values).
- **Reusable:** Localhost trust via `X-Forwarded-For: 127.0.0.1`, spoofed `User-Agent`, and **duplicate headers** (one for the proxy, one for the app) are recurring bypasses. Enumerate what each layer checks.

### PHP `base_convert` eval filter bypass RCE — **HackerLab2023**
- **Repo:** `Web/PHP2.md`
- **Mechanism:** `eval()` on input restricted to `[a-z_]` words with only `base_convert` whitelisted and ≤180 chars. Build function names numerically: `base_convert(55490343972,10,36)()` = `phpinfo()`; `base_convert(1751504350,10,36)(base_convert(661,10,36))` = `system('id')`; use `chr()` built the same way for spaces/slashes.
- **Reusable:** PHP "math-only" eval jails fall to `base_convert`-as-function-name-generator + `chr()`. A staple of francophone PHP web challenges.

### Python-as-filename upload RCE + `globals()` jailbreak — **HackerLab2023**
- **Repo:** `Web/Upload me.md`
- **Mechanism:** Uploaded **filename is executed as Python**. Comment out the extension with `#.png`. `import`/`class`/`subclasses`/`os` blacklisted; `globals` is not → `globals().values()[0].__dict__['__import__']('os')`, and defeat the `import`/`os` string filter by **base64-decoding** the names: `'X19pbXBvcnRfXw=='.decode('base64')`.
- **Reusable for NCTF finale:** Same core trick as pyjails (below) — when `__import__`/`os`/`open` are string-filtered, pass them base64-decoded; `globals()` is a common un-blacklisted pivot.

### `.git` exposure → source/secret recovery — **HackerLab2023**
- **Repo:** `Web/MAINTENANCE.md` — feroxbuster finds `/.git/`, dump with GitTools **git-dumper**, follow `.git/config` to an upstream GitHub repo, read secrets in old commits/branches (flag was hex-encoded in a commit message).
- **Reusable:** Always `feroxbuster`/`gobuster` for `/.git/`, `/.svn/`, backups; dump and read **commit history + all branches**. Flags are frequently hex/base64 in commit messages.

### JS source / client-side auth leak — **HackerLab2023**
- **Repo:** `Web/Source.md` — flag chained through commented hex in `utils.js`, decoded (ASCII→hex→hex) via dcode. Client-side-only "authentication" is a recurring 70-pt trope.

### 404CTF-2026 / StarHackademINT web style (official)
- **Repos:** `HackademINT-404CTF-2026/Web/` (5 challs), `AnouarVision-ctf-writeups/StarHackademinINT/2026/Web/` (`BoutiqueSuspecte1`, `FlappyOzgur`, `PasCroisable`, `Web101`).
- **Reusable:** French official events lean toward e-commerce logic flaws, client-side game-score tampering, and "intended-vuln chain" webapps. Solutions for StarHackademINT are in the Anouar repo (EN+IT) if you need worked examples.

---

## Crypto

### HAWK lattice signature — secret basis recovery from Gram matrices — **0xfun 2026**
- **Repo:** `paveledits-Writeups/0xfun CTF 2026/crypto-baby_HAWK/Writeup.md` (+ `solve.py`)
- **Mechanism:** Secret basis `B=[[f,F],[g,G]]` over `K=Q(zeta_256)`; public = Gram matrices `Q=B.H*B`, `S=B*B.H`, and AES-CBC(flag, key=sha256(str(sk))). Recover `B` to get the key. BKZ on the 256-dim lattice is too slow at n=128; instead use **both** `Q` and `S`: `det(B)=1` gives free inverses, equate `B*Q^-1 = S^-1*B = B^-H` to get 8 equations **linear** in `(f,g,F,G)`; model multiplication as **negacyclic convolution** (128×128 integer matrices) → one `1024×512` integer system, LLL on its 128-dim kernel, filter by known norms `||f||²+||g||²=q0[0]`, then brute the 256-th-root-of-unity ambiguity for the AES key.
- **Tools:** SageMath (`sage -python`), LLL.
- **Reusable for NCTF finale:** For structured-lattice crypto (HAWK/NTRU/Falcon-like), **convert to an exact linear system first** (use every public relation + `det=1`) and run LLL only on the small kernel instead of blind BKZ. Watch for root-of-unity/sign ambiguities when a hash of the raw secret is the key.

### RSA from `p+q` (Vieta) and chosen-plaintext against a public key — **HackerLab2023**
- **Repos:** `Cryptography/RSA.md` (given `x=p+q`, so `phi = n - x + 1` → decrypt directly), `Cryptography/Split_RSA.md` (message split **char-by-char**, each ciphertext is RSA of one ASCII char → encrypt all printable chars with the public key and match).
- **Tools:** `Crypto.Util.number`, RsaCtfTool (`--dump`), factordb.
- **Reusable:** When a hint gives `p+q` (or `p-q`), use `phi=n-(p+q)+1`. **Per-character RSA** (tiny message space, deterministic, no padding) is trivially broken by a dictionary of encryptions — recurring African-CTF RSA trope.

### AES-CBC IV recovery via chosen key (bit-flip math) — **HackerLab2023**
- **Repo:** `Cryptography/Messag_cipher.md` — "Admin" gate requires guessing the random IV. You can set your own 32-byte key and encrypt chosen plaintext. Since you control the key, locally decrypt the server ciphertext with any IV to recover `DEC = fakeplain ⊕ myiv`, then `IV = plaintext ⊕ DEC`. Tools: pwntools, PyCryptodome.
- **Reusable:** CBC `IV = P₀ ⊕ D(C₀)`. If the oracle lets you fix the key and feed chosen plaintext, you recover the server's "secret" IV with algebra, not brute force.

### Hash-per-character dictionary crack & multi-hash messages — **HackerLab2023**
- **Repos:** `Cryptography/Multi.md` (each line is MD5 or SHA256 of a single char — length tells which; brute `string.printable`), `Misc/5ive.md` (hash with a typo'd `O` char — remove it, then CrackStation), `Forensic/Forensic1.md` (NTLM `hashdump`→`john --format=nt` rockyou).
- **Tools:** CrackStation, `name-that-hash`, john, hashcat (see the `OneRuleToRuleThemStill` rules repo referenced in the sources manifest).
- **Reusable:** Short-domain hashes (single char/word) → brute the whole charset in a 10-line script. Always sanity-check hash strings for typo chars before giving up.

### Cipher-recognition / encoding chains (dCode + CyberChef) — **HackerLab2023**
- **Repos (Cryptography/):** `Clef de l'Histoire.md` (Vigenère, key = themed `DAHOMEYAHOSI`), `Atom.md` (atomic-number encoding), `Quelques traits dans ma lettre.md` ("Traits des Lettres"), `Five o'clock.md` (binary circular rotation), `Encoding.md` (star-separated hex), `Fashion.md` (**Ook!** esolang → Python using random.seed), `Pivot.md` (Vigenère brute), `Mateau de Tor.md` (ROT13 on JPEG **bytes**), `Anonyme.md` (GPG/PGP private key with l33t passphrase `4N0NYM0U5`).
- **Tools:** dCode "reconnaître un chiffrement", CyberChef, gpg.
- **Reusable for NCTF finale:** **The challenge name is the hint** (rot/atom/traits/fashion→Ook). Run unknown strings through dCode cipher-ID + CyberChef Magic first. Themed Vigenère keys draw on Dahomey/Benin history — expect Togo/Benin cultural keywords in NCTF.

### PRNG reconstruction & uninitialized-RNG predictability — **HackerLab2023**
- **Repos:** `Cryptography/Fashion.md` (recover flag from `random.choices` output by matching per-seed permutations across seed range 0–1337), `Reverse/RandomisRandom.md` (C `rand()` never seeded → first value is always `0x6b8b4567`; XOR back).
- **Reusable:** Unseeded C `rand()` is fully predictable (`0x6b8b4567` first). Python `random` with a small seed space is brute-forceable by replaying `random.seed(i)`.

### Fernet + OSINT malware-config recovery — **HackerLab2023**
- **Repo:** `Cryptography/Malconda.md` — a `gAAAA...` Fernet token; the hint pseudonym `hmzakhalid` → GitHub "Polymorphic-Virus-Python"; swap the challenge token into the original virus code, run (in a sandbox) to let it Fernet-decrypt with the embedded key.
- **Reusable:** `gAAAAAB...` = **Fernet**. Pseudonyms in challenge text are OSINT→GitHub leads; the decryptor is often the author's own public tool.

### 404CTF-2026 crypto surface (official sources)
- **Repo:** `HackademINT-404CTF-2026/Cryptanalyse/` (7): `What-the-hellman` (DLP/Diffie-Hellman), `Too-big-or-too-small` (RSA bounds/Coppersmith), `CHAesT` (AES), `2B-or-not-to-be`, `Dur-à-CERNer`, `Pas-tres-discret`, `Dejeuner-à-lANSSI`. Plus a whole **`AlgorithmiqueQuantique`** category (6 challs incl. `chall_shor` — Shor's algorithm, Qiskit). StarHackademINT crypto solutions (Anouar repo): CBC, RSA variants, substitution.
- **Reusable:** Top-end French crypto = DLP/Hellman, Coppersmith-size RSA, AES modes, **and quantum (Qiskit/Shor)**. If NCTF has a "quantum" track, expect Qiskit circuits + Shor factoring.

---

## Reverse Engineering

### Constant-XOR / arithmetic flag checks — reverse the transform — **HackerLab2023**
- **Repos (Reverse/):** `Beginner.md` (`(i*4 + 0x4768243) & 0xff ^ input[i] == target[i]` → XOR back), `RandomisRandom.md` (unseeded `rand`), `Siká-netic.md` (subtract `0x50` from a byte array), `Custom_Encryption.md` (XOR + bit-rotate + `+42 mod 256` + bit-inversion — invert each step), `Fake.md` (gdb breakpoint on `strcmp`, read real flag from `rdx`).
- **Tools:** Ghidra, gdb.
- **Reusable:** Most African-CTF rev = **static byte array + reversible per-char transform**. Decompile in Ghidra, transcribe the check, invert it in Python. For `strcmp`-style checks, breakpoint and read the register instead of reversing math.

### Hash-segment brute with crunch + inner cipher — **HackerLab2023**
- **Repo:** `Reverse/Couvent_des_initiés.md` — `Tinkpon()` takes 1–4 char groups, applies none/XOR/Caesar, hashes (SHA1), mangles (drop first byte, append `00`), compares. Brute each segment with `crunch`-generated wordlists, then invert the Caesar rotation (`R_ = 26 - R`).
- **Reusable:** Segment-wise hash checks are brute-forceable per-group with `crunch`. Combine with per-char cipher inversion.

### 404CTF-2026 RE / hardware surface (official sources)
- **Repo:** `HackademINT-404CTF-2026/RetroIngenierie/` (incl. `du-chameau-au-coq` — likely OCaml/Rust or arch-swap) and **`SecuriteMaterielle/`** (4 — hardware security: likely fault/glitch, side-channel, or firmware). StarHackademINT Reverse (Anouar): `BasedCrackme`, `CrackmeEasy/Medium`, `DansLaFoule`.
- **Reusable:** Expect a hardware-security track (SecuriteMaterielle) — relevant to the OT/ICS themes you already track. Crackmes dominate the entry tier.

---

## Forensics / DFIR

### Volatility memory forensics playbook — **HackerLab2023** (6+ challenges)
- **Repos (Forensic/):** `Investigation1.md` (`imageinfo`→`pslist`, process that started+stopped = `FoxitPDFReader`), `Investigation2.md` (`cmdline` for opened file), `Investigation3.md` (`filescan`+`dumpfiles -Q <offset>` to extract a `.txt`), `Forensic1.md` (`envars` for hostname/user, `hashdump`→john NTLM), `Forensic2.md` (`pstree` → cmd.exe parented by Winrar.exe; fix the +1h timezone skew via `imageinfo`), `Forensic3.md` (`netscan`+`cmdscan` → attacker IP:port + base64 C2 string).
- **Tools:** Volatility (Win7SP0x86 profile), grep, john.
- **Reusable for NCTF finale:** Standard Volatility order: `imageinfo → pslist/pstree → netscan → cmdscan/cmdline → filescan → dumpfiles → hashdump`. Suspicious parent (Winrar/Office spawning cmd/powershell) is the lead. Watch timezone skew between `imageinfo` image-time and process-start-time.

### Windows registry forensics (Eric Zimmerman) — **HackerLab2023**
- **Repos:** `Forensic/Artefact.md` (SAM `Domains\Account\Users`, Account-disabled + Last-Login), `Forensic/Last_Action.md` (NTUSER.DAT `…\Explorer\RecentDocs` for most-recent file/folder).
- **Tools:** Registry Explorer. **Reusable:** SAM = users/login; NTUSER RecentDocs = recent activity; UserAssist/ShimCache for execution.

### Encoded PowerShell in EVTX logs — **HackerLab2023**
- **Repo:** `Forensic/Intrusion.md` — `evtxexport` the `.evtx`, find base64 PowerShell, decode (`FromBase64String` + `DeflateStream`), run **only the decoder sub-expression** in a sandbox to avoid executing the payload.
- **Reusable:** EVTX → look for 4104/4688 PowerShell; decode base64+gzip/deflate; never run the full script — isolate the decode step.

### Android SQLite SMS/MMS forensics — **404CTF-2026**
- **Repo:** `AnouarVision-ctf-writeups/404CTF/2026/Forensics/CurieuxSMS/writeup-en.md`
- **Mechanism:** Three `mmssms.db` with different schemas (legacy AOSP `sms`, modern Google-Messages `conversations` cache, full AOSP `pdu`/`part`/`addr`). Flag split across tables + an MMS JPEG attachment in `app_parts/` + a suspicious `pdu.sub` subject field. "Deleted" messages survive in the `conversations` cache.
- **Reusable:** Know the Android telephony DB schemas; deleted rows persist in caches; attachments live in `part`/`app_parts`. Theme "Marie Curie / radium" = French-science flavor matching 404CTF.

### PCAP intrusion reconstruction + CVE identification — **404CTF-2026**
- **Repo:** `.../Forensics/ExfiltrationKantik1/writeup-en.md`
- **Mechanism:** Wireshark Statistics→Conversations to ID attacker/victim; `http.server contains "Apache"` for version; Follow-TCP-Stream of Telnet reveals `USER=-f root` → **telnetd auth bypass CVE-2026-24061** (inetutils passes `-f` to `/bin/login` = passwordless root); then cron + `authorized_keys` persistence + reverse shell to `:4444`.
- **Tools:** Wireshark, tshark. **Reusable:** Reconstruct attacker TCP streams; map observed commands to a CVE; flags are often `IP_IP_version_CVE_port` tuples. Telnet `USER=-f` is a live-looking realistic bug worth memorizing.

### DNS-tunneling base32 exfil — **404CTF-2026**
- **Repo:** `.../Forensics/ExtractionD'ADNs/writeup-en.md` — typosquat domains (`goog1e.com`, `y0utube.com`) carry base32 subdomains; concatenate all query subdomains **in order**, pad once at the end, `base64.b32decode` → a WebP (`RIFF…WEBP`) image. Tool: tshark `dns.flags.response==0`.
- **Reusable:** DNS tunneling = concatenate subdomains, decode as one base32 stream (pad only at the end), then file-carve by magic bytes.

### Steganography / file-structure repair — **HackerLab2023** (rich)
- **Repos (Steganography/ + Forensic/):** `Artofhiding:IDAT.md` (**reorder scrambled PNG IDAT chunks** per a given permutation; then morse in red pixels), `Nuxoxo.md` (**edit IHDR width/height** in a hex editor, then recompute the IHDR **CRC** via nayuki inspector; braille message), `Atinkpòn.md` (fix gzip header **flags byte** `0x89→00`; nested gzip→tar→steghide/FFD9-trailer/base64), `Custom.md` (**stegseek/steghide** with a crunch-generated hex-charset dict), `QR.md` (zip2john+rockyou; **merge GIF frames** horizontally into a scannable QR), `Ricky.md` (binary text forms a QR; `sed` 1→space), `weird_lsb.md`/`show_me.md`/`zinflu.md` (LSB / zlib).
- **Tools:** bless/hex editor, `file`, binwalk, zsteg, stegseek, steghide, crunch, zip2john, PIL, nayuki PNG chunk inspector.
- **Reusable for NCTF finale:** PNG surgery is a theme — **IDAT reorder, IHDR dimension + CRC repair, gzip flag-byte repair**. Corrupt-file challenges = fix the header/CRC to the spec. GIF/animated QR → merge frames. Steghide always → stegseek + crunch dict (hint describes the charset/length).

### 404CTF-2026 forensics/realistic surface (official sources)
- **Repo:** `HackademINT-404CTF-2026/InvestigationNumerique/` (curieux-sms, exfiltration-kantik 1–3, extraction-d-adns) and **`Realiste/`** (7 — `casse-toi-le-stagiaire`, `identite-de-bertillon`, `le-rayonnement-de-becquerel`, `protocole-pasteur`, etc. = boot2root/incident-response style).
- **Reusable:** "Réaliste" = multi-step realistic intrusion/boot2root with a French-science narrative; same shape as HackerLab Bénin's boot2root + Inception/Operation-Voile-de-Fer (2026 catalog).

---

## OT / ICS / Hardware

- **404CTF-2026:** `HackademINT-404CTF-2026/SecuriteMaterielle/` (4 hardware-security challenges — sources only; likely glitching/side-channel/firmware).
- **HackerLab Bénin 2026 (catalog):** `achbelsdn-Hackerlab-2026-quals/forensics/shockwave/README.md` — **SCADA network telemetry anomaly** on "TervaGrid"; `.../eaux-troubles/` — water-plant host compromise. These confirm an **OT/SCADA forensics** sub-theme in the 2026 Benin event.
- **Reusable for NCTF finale:** The 2026 African scene explicitly includes SCADA/OT (water grid, power grid narratives) and hardware security. Keep your existing OT/IEC-104/Modbus tooling and power-trace/side-channel playbooks ready; a "SCADA PCAP anomaly" forensics challenge is plausible. (No worked solutions available — statements/sources only.)

---

## Misc / Pyjail / OSINT / Esolang

### Python jails — filter-evasion object traversal — **HackerLab2023**
- **Repos:** `PWN/GANKPAME2.md` (30-char input, 11 tries; build a shell via `().__class__.__base__.__subclasses__()[-20]…__globals__['linecache']…['os']['system']('sh')`, splitting filtered strings `'sys'+'tem'`, `'line'+'cache'`, `'o'+'s'`), `Misc/Rabbit.md` (Python2 `input()` eval → `__import__('os').system(...)`).
- **Reusable for NCTF finale:** Pyjail staples — `().__class__.__base__.__subclasses__()` to reach `os.system`, **string concatenation / base64-decode to beat keyword filters**, and Python2 `input()` = eval. Short input limits → use `__builtins__` aliasing to shorten.

### Discord-bot abuse / platform logic — **HackerLab2023**
- **Repos:** `Misc/Admin_bot.md` (bot says "invite me + be admin" → **invite the bot to your own server** where you're admin via the OAuth `authorize?client_id=…&scope=bot` URL, then run `!password`), `Misc/Hacker Bot.md` (blind SQLi via bot, see Web).
- **Reusable:** On this scene, **Discord bots are challenge surfaces** (OAuth invite tricks, SQLi, prompt games). NCTF finale is Discord-adjacent — watch for bot-based challenges.

### Encoding/visual misc — **HackerLab2023**
- **Repos:** `Misc/M3ssage.md` (`file`→zlib → `zlib inflate`→from-hex), `Misc/DesiGn.md` (CSV X/Y → matplotlib scatter spells the flag), `Misc/Mr. Cat, I farted.md` (ChatGPT **share UUID** → `chat.openai.com/share/<uuid>`), `Misc/Ricky.md` (binary→QR), `Cryptography/Hackerlab.md` (zero-width `‌/‍` → binary → bytes).
- **Reusable:** `file` + CyberChef "Magic" solves most misc. Coordinate CSVs → plot them. Zero-width unicode = binary. Odd UUIDs/URLs may be OSINT pivots (ChatGPT/Discord/GitHub).

### 404CTF OSINT = French historical/geo deep-dives — **404CTF-2026**
- **Repos (`AnouarVision-ctf-writeups/404CTF/2026/OSINT/`):** `CanularSavant1-3` (Paris landmark full name → Twenty One Pilots "Morph" lyric → Nicolas Bourbaki → André Weil via birthday + **sun-alignment with Arc de Triomphe** using SunTrace3D), `C'EtaitCache` (censored GitHub screenshot → `alice-recoque` → clone repo, read git history), `DoctorEsLangues` (Wayback Machine old CV), `Papioutai` (ENS `archicubes.ens.fr` alumni directory + **Mémoire des Hommes** WWI database), `MetroOSINTDodo` (Paris metro routing by travel time).
- **Tools:** Google, Wikipedia, Wayback Machine, Genius lyrics, SunTrace3D, ENS directory, Mémoire des Hommes, git history.
- **Reusable for NCTF finale:** French/African OSINT rewards **official-name precision** (Wikipedia disambiguation), **Wayback Machine** for changed pages, **git commit history** on leaked repo names, specialist registries (alumni, war-dead, transit). Flags demand exact spelling/accents.

---

## Most-repeated techniques — NCTF finale quick checklist

Ordered by how often they recur across these African/francophone CTFs (⇒ highest predictive value for NCTF):

1. **Decompile → reverse a per-char transform** (XOR/add/rotate against a static array) — the single most common rev pattern (Ghidra + invert in Python).
2. **Volatility memory-forensics chain** (`imageinfo→pslist→netscan→cmdscan→filescan→dumpfiles→hashdump`) + Registry Explorer (SAM/NTUSER). DFIR is heavily weighted.
3. **PNG/file-structure repair** — IDAT reorder, IHDR dimension+CRC fix, gzip flag-byte fix; `file` + magic-byte carving for any "corrupt" file.
4. **SSTI `{{7*7}}` → `__globals__` RCE** (Flask) and **XXE `file:///`** — the default web-RCE probes.
5. **JWT weak secret → `john`/`hashcat` → re-sign (JWT Editor) → IDOR** on an in-token id.
6. **Filter/jail bypass by string-splitting + base64-decode** — identical trick across pyjail, PHP `base_convert`, Node LFI, SQLi keyword filters, upload-RCE.
7. **Cipher/encoding ID via dCode + CyberChef Magic**, with **the challenge name as the hint**; themed Vigenère keys (Dahomey/Benin/Togo history).
8. **RSA shortcuts** — `phi=n-(p+q)+1`, per-character chosen-plaintext, factordb/RsaCtfTool; plus LLL-on-kernel for structured lattices (HAWK).
9. **Hash cracking** — short-domain char/word brute, NTLM `hashdump`+john+rockyou, zip2john/`name-that-hash`; keep the `OneRuleToRuleThemStill` hashcat rules handy.
10. **SUID/`.so` hijack + boot2root privesc** (`ldd` writable lib, `setuid(0);system()`); watch for the "Réaliste"/boot2root multi-step narrative.
11. **SSRF/XSS via URL-parser confusion** (`@attacker.com`, `file:///http/../../flag.txt`) + ngrok OOB exfil against admin bots.
12. **Discord-bot challenges** (OAuth invite abuse, bot-mediated SQLi/prompt games) — Discord-native scene.
13. **`.git` exposure → git-dumper → secrets in commit history/branches.**
14. **Pcap intrusion reconstruction → map to a CVE** (e.g. telnetd `USER=-f` CVE-2026-24061) + DNS-tunneling base32 exfil.
15. **OSINT precision** — Wayback Machine, Wikipedia exact names, specialist registries; French accents/spelling matter.
16. **Watch the high end:** kernel pwn (QEMU/initramfs, task_struct cred overwrite, seccomp strip), heap (tcache safe-linking, House of Einherjar on glibc 2.42), quantum (Qiskit/Shor), and hardware-security (SecuriteMaterielle) tracks appear at 404CTF-level events.

### Unfetched / flagged
- **NICCTF-2026 Notion** page could not be read (JS-only / 307→app.notion.com, only the "Notion" title rendered). Re-try with a headless browser (`claude-in-chrome` / Playwright) if its content is needed.
- **achbelsdn HackerLab-2026 quals**: statements/metadata only — **no solutions committed** (all "À compléter"). Useful for taxonomy/theme, not for techniques.
- **HackademINT/404CTF-2026** official repo = challenge **sources**, not writeups; technique inferences for its unsolved challenges are from category/filenames + the Anouar solved subset.
- ExifTool RCE (below) is from the kore.one blog, cross-referenced to the paveledits 0xfun folder which contains only the `baby_HAWK` crypto writeup (no `shell` writeup committed).

### Bonus — ExifTool DjVu RCE (0xfun "Shell") — **kore.one blog**
- **Source:** https://kore.one/0xfun-ctf-2026-shell-challenge-writeup/
- **Mechanism:** Image-upload app runs **ExifTool 12.16** (vulnerable to **CVE-2021-22204**); a DjVu file embedded in a JPEG's EXIF is parsed recursively and its annotation data is eval'd as Perl → RCE. File-type check passes; flag returned in metadata output.
- **Tools:** DjVuLibre, exiftool, ImageMagick, python requests.
- **Reusable:** Any "upload image → see metadata" flow = try the ExifTool DjVu RCE (CVE-2021-22204). Metadata parsers are RCE surface; extension/type checks don't stop embedded payloads.
