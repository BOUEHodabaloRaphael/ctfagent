---
doc_kind: writeup
title: "AFRICC 2027 Qualifiers — full writeup (BOUE Hodabalo Raphael, Togo)"
category: misc
slug: africc2027-quals-full-writeup
created: 2026-11-03
status: solved
tags:
  - africc
  - pwn
  - web
  - crypto
  - rev
  - forensics
  - misc
  - boot2root
  - osint
  - fsop
  - heap
  - seccomp
  - prototype-pollution
  - ssti
  - jwt
  - idor
  - nginx-path-traversal
  - rsa
  - reverse-engineering
  - md5-length-extension
  - ssrf
source: "AFRICC 2027 Qualifiers (own competition writeup)"
target: "multiple (per-challenge, see body)"
---
# AFRICC 2027 Qualifiers — full writeup (BOUE Hodabalo Raphael, Togo)

## Challenge Summary

- Source: AFRICC 2027 Qualifiers, PDF writeup `writeup-africc2027_BOUE_Hodabalo_Raphael_TOGO_English Version.pdf` in `~/Downloads/`, read page by page (native text PDF, no OCR needed).
- Target: ~22 challenges solved across Pwn, Web, Crypto, Reverse Engineering, Forensics, Misc (polyglot series), Boot2Root, OSINT, Blockchain.
- Goal: capture the techniques as a reusable CTF reference for future events (NCTF26 and beyond) — this file is a technique index, not a step-by-step walkthrough; see Payloads And Commands for the condensed actionable recipes per challenge.

## Initial Signals

- Entry point: author's own full writeup PDF, organized by category with flag table + per-challenge vulnerability/exploitation sections and terminal transcripts.
- Visible hints: author self-rates Pwn as strongest category; several challenges are deliberately "decoy-first" (a misleading hint in the description, real vuln lies elsewhere — recurring theme worth noting generally).
- First confirming probe: n/a (reading a finished writeup, not live probing).

## Exploit Chain

(Each challenge is its own short chain; grouped by category below instead of one linear sequence.)

### Pwn

1. **secrets (300pts)** — heap UAF menu (alloc/edit/delete/show) → leak heap address via use-after-free (show-after-delete) → compute libc base from unsorted-bin offset → leak glibc's safe-linking XOR mask (`chunk_addr >> 12`, glibc ≥2.32) via a second UAF → tcache-poison the freed chunk's `next` pointer (XORed with the recovered mask) to point at `_IO_2_1_stdout_` → forge a fake `FILE` structure: **vtable field stays the authentic `_IO_wfile_jumps`** (protected by `IO_validate_vtable`), while **`_wide_data` (offset 0xa0, unvalidated) points to a forged `_IO_wide_data` struct** whose `_wide_vtable` points to a fake jump table where `__doallocate` is replaced with `system("/bin/sh")`. The next implicit `puts()`/stream flush triggers the corrupted stream's buffer allocation, running `system()` — **no GOT write, so Full RELRO is irrelevant**. This is the core of the modern FSOP (File Stream Oriented Programming) technique on glibc ≥2.34 (post `__malloc_hook`/`__free_hook` removal).
2. **bmpcheck (200pts)** — Flask webapp uploads a BMP to a SUID-root `verify` binary. `biSizeImage` (offset 0x22 of BMP header) controls how many bytes `fread()` reads into a 16-byte `alloca()` buffer → classic stack buffer overflow via an oversized declared image size, independent of the actual file size. `checksec` falsely reports a canary (present elsewhere in the binary, **not in `main()`**) — confirmed by running unprivileged: `chroot` fails, `perror()` → `write(2,...)` → killed by seccomp (SIGSYS), proving the write syscall itself is blocked. **The real obstacle: a seccomp filter kills 17 data-output syscalls** (`write`, `send*`, `splice`, `copy_file_range`, `execve*`...) — reading is allowed, exfiltrating the bytes is not. Chain: (1) overflow `alloca()` buffer with a custom ROP chain (static binary, no PIE); (2) **"fclose trap"**: repair the overwritten `FILE*` to point at `&_IO_2_1_stderr_` (a fixed address) so `fclose()` becomes harmless and `ret` can jump into the ROP chain instead of crashing; (3) escape the `chroot("/tmp/files")` jail via `mkdir` + `chroot` into a subfolder + 30× `chdir("..")` + `chroot(".")` to climb back to the real root; (4) `open()`+`read()` the `/flag` file into a BSS buffer (still can't exfiltrate it directly — no output syscalls); (5) **exit-code oracle**: the app exposes `success = (returncode == 0)`. The ROP chain compares `flag[i]` against a guessed byte then calls `exit_group(result)`: exit code 0 iff the guessed character is correct — a blind boolean oracle brute-forceable remotely, one byte at a time, entirely through process exit codes.

### Web

1. **securenot3s (50pts)** — description baits a Jinja2 SSTI via "title field" (decoy); real bug is a **JavaScript prototype-pollution via `__proto__[outputFunctionName]`** in a custom query-string parser, which controls the function name EJS 3.1.6 generates at compile time (the CVE-2022-29078 pattern). Controlling `outputFunctionName` injects arbitrary JS that *executes* server-side instead of being merely interpolated → RCE via a crafted `__proto__[outputFunctionName]=x;__output+=execSync(...).toString();x` query param.
2. **africcro0m (300pts)** — misconfigured nginx `alias` directive without an isolated trailing slash → classic **"off-by-slash" path traversal** (`/assets/../server.py` serves the file outside the intended web root). `curl --path-as-is` (bypasses client-side normalization of `../`) leaks the full Python source, which contains hardcoded creds + a static token → log in → use the token on the admin panel to read the flag directly.
3. **Deputy's Ledger (200pts)** — multi-tenant app addresses resources by an `org_id` passed in the request, **never checking the authenticated user's org actually owns it** — classic IDOR/BOLA. Enumerate `org_id=1..20` with a valid session cookie; flag sits in another org's journal (`org_id=7` here).
4. **Confused Deputy (100pts)** — JWT signed RS256, public key exposed via a `/jwks.json` (or `/publickey`) endpoint; verifier accepts whatever `alg` the token header states without constraining it → classic **RS256→HS256 algorithm-confusion**. Replay the RS256 public key (exact PEM bytes) as the HMAC secret, forge an HS256 token with `role=admin`, server validates it as authentic since it uses the same public key material to verify both algorithms.

### Crypto

1. **Twin Spirit Channels (200pts)** — RSA decryption oracle randomized by a Blum-Blum-Shub (BBS) generator between two oracle types (a parity oracle and a threshold/MSB oracle), but the mathematical identity `parity(m_j) == threshold(m_{j-1})` for an odd modulus `n` lets you break the system **without knowing in advance which oracle type answers which query**. Chain: craft an always-informative query to recover the BBS generator's internal state → brute-force the 15-bit BBS prime seed (restricted search space, primes ≡ 3 mod 4) → precompute the full future oracle-type sequence once the seed is known → adaptive queries reconstruct the plaintext's binary fraction bit by bit.
2. **Lattice Recall / PoW (200pts, no real flag points — a proof-of-work gate)** — custom block-based PoW: for each of 4 rounds, find two keys (`k1`, `key2bytes`) such that a custom hash function (`phash`) lands on 0; final result combines the 4 rounds via `h = (h2 * u * z) & 2**32`. The per-byte transform `h = (2*(h ^ (a+b+c-d))) & m` through a bijective s-box means **every target byte `d` is reachable** — solved via candidate `k1` values + a random walk until the result lands on the right divisibility target, not a closed-form inversion.

### Reverse Engineering

1. **The Warden (200pts)** — a Windows utility validates a license key passed as an argument; the key is trivially recoverable in plaintext and *works*, but the flag isn't the key — the real protection is a **TLS callback** (executed before `main()`, referenced only via `IMAGE_TLS_DIRECTORY`, nearly invisible to casual analysis). The callback does a double anti-debug check, reads `TimeDateStamp`/`SizeOfImage` from the PE header to derive 16 keys via a TEA-style schedule, and decrypts a 56-byte blob through a 16-round Feistel network with a 4-bit S-box. If a debugger is detected, one key gets silently bit-flipped (corrupting the schedule without crashing — a quiet anti-debug trap to watch for). Since the program never reveals the decrypted content at any observable point, **the only path is reproducing the entire algorithm bit-exact in Python** from pure static analysis (no dynamic extraction possible without defeating the anti-debug first, and even then nothing prints it).
2. **Fortr3ss (200pts)** — binary visibly contains an `Africc{` string in plaintext, but it's a **decoy**: XOR-obfuscated blob, not the real flag. The actual flag is derived dynamically by the verification function (`check_part`, reversed via radare2 at a specific offset) — reconstruct the per-byte derivation algorithm and replay it in Python against the stored blob to get the real plaintext.
3. **dej4 VM (300pts)** — small custom bytecode VM implementing a CBC-like block cipher over 32 bytes (2×16-byte blocks) through an ARX core (Add-Rotate-XOR) running 3000 rounds. `vm_run` (the VM's core interpreter) was reversed instruction-by-instruction to write its exact **inverse** function in Python: feed each ciphertext block into the inverse to recover the pre-XOR internal state, then XOR with the IV (block 0) or the previous block's ciphertext (block 1, CBC chaining) to recover plaintext.
4. **d3lulu (50pts)** — binary computes an FNV-1a hash of the input, XORs it with a constant, then a floating-point LCG decides position-by-position whether a "base character" (a fixed table stored in the binary) gets conditionally XORed with `0x1f`. **The twist/lesson ("hallucination"): the check looks complex (hash + LCG + conditional XOR), but the base-character table, read directly from the binary without ever applying the conditional transform, already IS the plaintext flag** — the elaborate verification is a decoy wrapped around already-readable static data. General lesson: before fully reversing a complex-looking check, try reading any statically-embedded "base"/"default"/"seed" table as-is — it sometimes already is the answer.

### Forensics

1. **Silent Echo (50pts)** — pcap with suspicious ICMP (ping) traffic; exfiltration channel hidden in the **ICMP `identifier` field** of echo-request packets (2 usable bytes per packet, repurposed to carry data instead of its normal randomized-per-session value). Extract the identifier-field sequence across all ICMP packets (`tshark -Y "icmp && icmp.ident != <normal-session-value>" -T fields -e icmp.seq -e icmp.ident`), reassemble 2 bytes per packet in order → base64 → gzip → plaintext flag.
2. **The Intruder (75/150pts)** — full compromise chain in a pcap + shell session: `User-Agent: Mozilla/5.0 (Hydra)` on hundreds of sequential `POST /login` = THC-Hydra brute-force signature; filter HTTP 302 responses to find 3 distinct successfully-reused credential pairs; probe `{{7*7}}` confirms Jinja2 SSTI as the app vuln; attacker's own message left in `history`; SUID-root binary path found in a captured Dockerfile reveals the privesc vector.
3. **NordVault Trap** — password recovered via `grep -riE "swift[_-]?pass|password" <dump-dir>` over provided artifacts/config files — reminder to always grep broadly for common secret-naming variants before assuming a harder crypto step is needed.

### Misc — polyglot series (5 progressive challenges, 1000pts total)

Common theme: write **one single source file simultaneously valid and functionally identical in 6 languages** (Python 3, Perl, Ruby, PHP 8, C, C++), with increasingly strict constraints at each stage (no shell calls → no quotes/brackets → no digits → ≤512 bytes and ≤25 parentheses). Key techniques: `<?php ... __halt_compiler(); ?>` to silence PHP's trailing output; exploiting different numeric coercion between Perl (`"b"+"" == ""`) and Python/Ruby for a 3-way branch; Ruby treats `nil`/`false` as falsy but not `0` (unlike Python) — swap in an empty string for the no-digits variant; `__DATA__`/`__END__` combined with Python triple-quote docstrings to hide the C code from the scripting languages, all wrapped in C `/* ... */` comments; minimize parenthesis count using each language's alternate syntax forms (`open FH,"file"` in Perl, `File.read "file"` in Ruby, `include"file"` in PHP, `fread`+`puts` instead of a byte-by-byte loop in C).

### Boot2Root

1. **Kaldvik (75pts)** — 5-stage chain on a single box: **(1) SSRF filter bypass**: the `/api/link/probe` endpoint only validates the hostname pattern (`*.kaldvik.local`) but resolves DNS normally — a `nip.io` subdomain (`fleet.kaldvik.local.127.0.0.1.nip.io`, which resolves to `127.0.0.1`) satisfies the regex while pointing at localhost. Port-scan internal services through the SSRF itself by looping candidate ports through the same probe. **(2) Forge a password-reset token**: leaked source reveals `token = sha1(f"{user}|{ts}|{install_id}").hexdigest()[:20]` — `install_id` leaks in an HTTP response header, `ts` is the server's Unix timestamp pulled from the `Date` response header (small empirical clock-skew adjustment needed) → recompute the token locally, POST it to reset the target user's password. **(3) SSTI → RCE**: a custom template engine filters attribute access in dot notation (`.__class__`) but **not in bracket notation (`['__class__']`)** — classic Jinja2-style sandbox bypass: `{% for c in incident['__class__']['__base__']['__subclasses__']() %}...{{ c['__init__']['__globals__']['os']['popen'](cmd)['read']() }}` to get command execution. **(4) Network pivot via a custom binary protocol (KVX1)** authenticated with `MAC = MD5(secret || message)` — inherently vulnerable to an **MD5 length-extension attack**: capture one legitimate signed frame (HELLO) from disk, reimplement MD5 compression manually to resume hashing from the *known intermediate state* (the captured MAC, reinterpreted as the internal `a,b,c,d` registers) and append attacker-chosen data (a new `exec` command) with correct padding — producing a **valid MAC for `secret || known_message || glue_padding || attacker_data` without ever knowing `secret`**. Secret length was unknown in advance; brute-forced and confirmed at 30 bytes. **(5)** read the flag from the newly-reached internal host.

### OSINT

1. **Discord: welcome (N/A)** — joined the CTF's official Discord via the invite link, looked up the challenge designer's profile; the flag was sitting in plaintext in their **custom status** on the profile card. General lesson: always check Discord custom-status/about-me/pinned-messages on org-affiliated accounts during OSINT recon, not just message history.

## Key Evidence

- `checksec --file=verify` showed "Canary found" globally but the overflow in `main()` was still exploitable — confirms per-function canary placement must be checked (e.g. via disassembly), not just the binary-wide `checksec` summary (bmpcheck).
- `seccomp-tools dump ./verify` output listing `KILL_PROCESS` on `write, pwrite64, writev, ..., sendfile, splice, ...` is what turned "stack overflow with a shell" into "must exfiltrate via a side channel" — the seccomp policy, not the overflow itself, was the actual difficulty (bmpcheck).
- `curl --path-as-is "https://TARGET/assets/../server.py"` returning HTTP 200 with the raw Python source is the exact confirming probe for the nginx off-by-slash misconfiguration (africcro0m).
- Successful `wine warden.exe "WARDEN-PROD-2024-XK19"` printing "License accepted" while the TLS callback runs silently underneath, with zero visible difference — the key lesson that a program accepting your input happily does not mean nothing else is happening (The Warden).

## Dead Ends

- Pursuing the Jinja2-SSTI hint given in `securenot3s`'s description directly — the description's stated vector was a deliberate decoy; the real bug (prototype pollution) was only found by reading the source.
- Assuming `bmpcheck`'s globally-reported canary applied to `main()` — it doesn't; checking per-function is what unblocked the overflow.
- In `Fortr3ss`, trusting the plaintext `Africc{...}` string found via `strings` as the flag — it's XOR-obfuscated decoy data, not the real (dynamically-derived) flag.
- In `d3lulu`, starting to fully reverse the hash+LCG+conditional-XOR check before checking whether the embedded base table was already readable as-is.

## Payloads And Commands

```bash
# nginx off-by-slash path traversal probe
curl -s --path-as-is "https://TARGET/assets/../server.py" -o server.py

# JWT RS256->HS256 alg-confusion forge (python-jose/pyjwt)
python3 - <<'EOF'
import jwt
pub = open("public.pem","rb").read()
tok = jwt.encode({"user":"admin","role":"admin"}, pub, algorithm="HS256")
print(tok)
EOF

# ICMP identifier-field exfil extraction
tshark -r capture.pcap -Y "icmp && icmp.ident != <normal_value>" -T fields -e icmp.seq -e icmp.ident > pairs.txt
# then: reassemble 2 bytes/packet in order -> base64 decode -> gzip decompress

# SSRF bypass via nip.io wildcard DNS against a hostname-regex filter
curl -sk -H "Host: real.target.local" \
  --data-urlencode "target=http://internal-host.target.local.127.0.0.1.nip.io:PORT/" \
  -G "https://TARGET/api/link/probe"

# MD5 length-extension attack (manual, no hashpumpy dependency) — forge.py sketch
python3 - <<'EOF'
import struct, hashlib
def leftrotate(x,c): x &= 0xFFFFFFFF; return ((x<<c)|(x>>(32-c))) & 0xFFFFFFFF
# standard MD5 s[] and K[] tables, then a md5_compress(chunk, state) reimplementation
# that resumes from a KNOWN intermediate state (a,b,c,d) = struct.unpack('<4I', known_mac_bytes)
# md5_padding(msg_len_bytes) reproduces MD5's own length-padding for the glue block
# forge(known_mac_hex, known_len, append_data) -> (new_mac, forged_message_suffix)
# Append forged_message_suffix to the original known_message; the new_mac verifies
# as secret||known_message||glue_padding||append_data WITHOUT knowing secret.
EOF
```

## Flag / Outcome

- All flags listed in the Challenge Summary table above (22 challenges, ~3650 points across Pwn/Web/Crypto/Rev/Forensics/Misc/Boot2Root/OSINT/Blockchain); two sub-questions lost (one Forensics sub-question banned after a wrong submission, one Pwn "secrets" flag was actually a fallback message from organizers due to infra instability — exploitation itself was confirmed complete via shell access, independent of the fallback flag text).

## Reusable Lessons

- **Decoy-first descriptions/strings are a recurring AFRICC pattern**: both a challenge *description* (securenot3s pointed at SSTI, real bug was prototype pollution) and an *embedded plaintext string* (Fortr3ss's visible `Africc{...}` was XOR-obfuscated decoy data) can be deliberately misleading — always verify a found "flag-shaped" string actually decodes/validates before trusting it.
- **`checksec`'s canary/mitigation summary is binary-wide, not per-function** — a reported canary can be entirely absent from the actually-vulnerable function; check the disassembly of the specific function before ruling out a stack overflow.
- **Seccomp can make a working overflow useless without a side-channel exfil plan** — always check `seccomp-tools dump` (or equivalent) early; if all output syscalls are killed, look for an exit-code, timing, or error-message oracle instead of a direct shell/output primitive.
- **`nip.io`/`sslip.io` wildcard-DNS services remain a reliable SSRF bypass** against hostname-allowlist regexes that validate the string but let DNS resolve freely to an attacker-chosen IP (including loopback).
- **MD5/SHA1/SHA256 length-extension attacks apply to any custom `MAC = H(secret || message)` construction** (not just textbook CTF crypto) — if a captured legitimate MAC can be reinterpreted as the hash's internal state and the secret length can be brute-forced/bounded, a valid MAC for attacker-appended data is forgeable without ever learning the secret. Always prefer HMAC over naive `H(secret||msg)` when designing/auditing a protocol — and always check for naive concatenation when attacking one.
- **A JWT exposing its RS256 public key without constraining the accepted `alg`** is exploitable identically every time via the HS256-with-public-key-as-secret forge — already captured as an existing pattern, see below.
- When a verification routine looks unusually elaborate for a Misc/Rev challenge, check whether the "obviously fake" intermediate data (a static table, a decoy string) is in fact already the answer before committing to fully reversing the elaborate path.

## Pattern Candidates

- Existing pattern to update: [`forge-jwt-rs256-hs256-alg-confusion.md`](../../patterns/web/forge-jwt-rs256-hs256-alg-confusion.md) (web) — this writeup's "Confused Deputy" challenge is a second independent confirmation of the same technique, worth a one-line cross-reference there.
- New patterns created from this writeup (see files below):
  - `knowledge/patterns/pwn/fsop-tcache-poison-fake-file-struct.md` — the `secrets` heap exploit chain.
  - `knowledge/patterns/pwn/seccomp-exit-code-blind-oracle.md` — the `bmpcheck` seccomp-bypass-via-exit-code technique.
  - `knowledge/patterns/misc/ssrf-bypass-nipio-wildcard-dns.md` — the Kaldvik SSRF filter bypass.
  - `knowledge/patterns/misc/md5-length-extension-custom-protocol-mac.md` — the Kaldvik KVX1 protocol forgery.
