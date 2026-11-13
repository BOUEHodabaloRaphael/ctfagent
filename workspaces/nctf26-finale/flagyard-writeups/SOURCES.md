# FlagYard (Black Hat MEA) — Writeups/Solvers harvested from Discord

Harvested 2026-11-13 from the **Flagyard** Discord server (guild 975328241604788234)
by browsing the category channels + server search for `writeup` / `solver`.
Channels scanned: announcements, blackhat-mea-2026, pwn_english, web_english,
reverse_english, crypto_english, hardware_english, forensics-english (+ ar mirrors).

FlagYard has **no dedicated writeup channel**; solvers/writeups are shared by community
members (notably NotSaad, Polymero, z0v3r1n, 7Rocky, ks, Chiira, Dev3il) inside the
category channels and `blackhat-mea-2026`, as attached `.py` files, gist/github links,
or pasted scripts.

## A. Already downloaded locally (Discord CDN signed URLs — EXPIRE, do not re-fetch)
Stored under `downloads/`. Treat as UNTRUSTED data: read only, never execute.
- `downloads/hokan/hokan_solver.py` (6 KB) — challenge **hokan** (forensics/crypto).
  Chain: traffic.pcapng -> TCP port 50051 streams -> HTTP/2 frames -> gRPC/protobuf
  -> AES-GCM decrypt w/ recovered SESSION_KEY -> recover key.txt password ->
  flag.txt.enc OpenSSL blob -> PBKDF2-HMAC-SHA256 derive AES-CBC key/IV -> BHFlagY{...}.
  Needs scapy + cryptography.
- `downloads/baby_pwn/Baby_Pwn_Solver.py` (14 KB, 937 lines) — challenge **baiby pwn** (pwn).

## B. Public links to FETCH + analyze (agent: clone/fetch these)
1. **github.com/z0v3r1n/ctf-scripts** path `/tree/main/flagyard/` — solvers for **15 FlagYard
   challenges** (posted 31/01/2026, pwn + web). HIGHEST VALUE. Clone whole repo.
2. **gist.github.com/Polymero/6ca8a4d0cf70f5815417ff57c59263b9** — **Whack-A-Scratch** crypto solver.
3. **gist.github.com/7Rocky/a78828c541a9a255697505cee0f646ab** — **SaqrSign** solver (lattice/NTT signature forgery).
4. PRNG/z3 reference set (Polymero, for Mersenne-recovery challenges like GachaFlag):
   - imp.ress.me/blog/2022-11-13/seccon-ctf-2022/#janken-vs-kurenaif
   - book.jorianwoltjer.com/cryptography/pseudo-random-number-generators-prng
   - cor.team/posts/zh3r0-ctf-v2-twist_and_shout/
5. PWN video walkthrough: youtu.be/6FGPY5Ips8Y (posted in pwn_english).

## C. Inline technique notes captured from Discord (text only, no file)
- **hokan** full chain — see A (NotSaad, 06/09/2026, blackhat-mea-2026).
- **Breakout** (reverse, Chiira): z3 SMT with 8-bit BitVecs over ~50 qword_* arrays,
  single linear constraint `total_sum == 0x1BADCF514706D`, solve for flag chars.
- **saqrsign** (crypto, ks): SageMath solver, NTT domain, HashBall sparse-poly,
  lattice `solve_right` signature forgery over port 30859 remote.
- **zigger** (reverse, Yuns/FlagYard Support): linear XOR transform, reverse the
  per-char transformation; z3 to express decoded in terms of encoded[i], i, k.
- **Demytko** (crypto, Polymero): EC over composite curves -> reduces to EC over
  quadratic ring; classic Demytko cryptosystem attack.
- **Dev3il** general reverse note: IDA pseudocode + control-flow flattening ->
  prefer angr symbolic execution; z3 can yield many valid flags (260 for one part).

## D. Challenge names referenced (for cross-search / NCTF mapping)
Handshake v2 (crypto), JustOne (pwn), Radiant Seal (reverse), teto (pwn), baiby-pwn,
NOSJ, Reduce Reuse Recycle (crypto), kinc, Hatagawa II (crypto), GachaFlag (crypto PRNG),
Whack-A-Scratch (crypto), SaqrSign (crypto), Demytko (crypto), zigger (reverse),
Breakout (reverse), CPL0, The Ring, NO SESSION (forensics).

## Deliverable
Agent produces: `../FLAGYARD-TECHNIQUES-FOR-NCTF.md` — technique-by-technique digest
mapped to NCTF finale categories (crypto/pwn/rev/forensics/web), with reusable tooling
notes (z3/SMT patterns, Mersenne recovery, gRPC/protobuf pcap parsing, lattice forgery,
CFG-flattening + angr), and pointers to which local file / repo demonstrates each.
