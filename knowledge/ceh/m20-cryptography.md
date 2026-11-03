# CEH v13 Module 20 — Cryptography (technique synthesis)

Source: `/home/kali/Downloads/CEH/CEHv13 - Module 20 - Cryptography hide01.ir.pdf` (258 pages).
Method: `pdftoppm -r 150 -gray -png` (whole PDF at once) then `tesseract --psm 3` per page via
`xargs -P 2` (native `pdftotext` is useless on this watermark-protected file set — confirmed on
M15 before adopting OCR). Offensive techniques / exact commands only, exam theory skipped.
Page numbers below are the module's own ("Module 20 Page NNNN", as OCR'd).

## 1. Cracking disk-encryption containers with hashcat (concrete, reusable) — p.3474-3475

Target: VeraCrypt (also applies to similar formats via hashcat `-m` modes). Full recipe:
```bash
# 1. Pull the first 512 bytes of the encrypted container header — this is the "hash"
dd.exe if=<path_to_container> of=<path_to_hashfile.tc> bs=512 count=1

# 2. Brute-force a numeric PIN/password with a hashcat mask (mode 13721 = VeraCrypt SHA512+XTS 512-bit)
hashcat.exe -a 3 -w 1 -m 13721 <path_to_hashfile.tc> ?d?d?d?d
#   -a 3   : brute-force attack mode
#   -w 1   : workload profile (1=low .. 4=high)
#   -m     : hash mode (13721 = VeraCrypt here; pick the mode matching the target cipher/KDF)
#   ?d?d?d?d : 4-digit numeric mask (swap for ?l?u?d?s per char class, or extend length)

# 3. Or brute-force with a wordlist instead of a mask
hashcat.exe -w 1 -m 13721 hash.tc wordlist.txt
```
On Linux, drop `.exe`. Same pattern (`dd` header extraction + `hashcat -m <mode>`) generalizes
to TrueCrypt, LUKS, BitLocker (FVEK) containers — only the `-m` mode number changes. John the
Ripper is the module's named fallback when hashcat isn't available (same workflow: extract
header → feed to `john`/`truecrack`-style cracker).

## 2. Cryptanalysis attack catalog (what to try, in order of practicality)

- **Ciphertext-only**: attacker has ciphertext only; look for statistical patterns (hardest, most
  realistic scenario — p.3465).
- **Known-plaintext**: have plaintext/ciphertext pairs, deduce the key (p.3467) — basis of
  **linear cryptanalysis** (known-plaintext, linear approximation of the cipher, p.3463): for 56-bit
  DES, ~2^43 known plaintexts beat a 2^56 brute force.
- **Chosen-plaintext**: attacker picks plaintexts, gets ciphertexts back — basis of **differential
  cryptanalysis** (examine how an input difference propagates to the output difference, p.3464).
- **Adaptive chosen-plaintext**: interactive, each query informed by the last response (p.3465).
- **Chosen-ciphertext**: pick ciphertexts, get plaintext back; variants = **lunchtime/midnight
  attack** (limited time/pairs) and **adaptive chosen-ciphertext** (p.3467). This is the family
  behind **padding-oracle** attacks (below).
- **Related-key attack**: exploit a mathematical relationship between two different keys, e.g.
  WEP's RC4+24-bit IV reuse — after ~4096 packets two parties share an IV/RC4 key due to the
  birthday paradox, enabling key recovery (p.3486-3487).
- **Dictionary attack**: precomputed plaintext→ciphertext/hash table built over time (p.3466).
- **Rubber-hose attack**: coercion/torture to extract the key — mentioned explicitly as a listed
  technique, not just a joke (p.3467).
- **Chosen-key attack**: break an n-bit cipher in ~2^(n/2) ops by choosing/relating keys (p.3467).
- **Timing attack**: repeatedly measure exact execution time of modular exponentiation to leak
  key bits (p.3467) — generalizes to any data-dependent branch/comparison.
- **MITM attack**: against the key-exchange phase of public-key protocols (p.3468).
- **Integral cryptanalysis**: extension of differential analysis — hold `b-k` bits constant, vary the
  remaining `k` bits through all 2^k values (useful against substitution-permutation networks,
  p.3464).
- **Quantum cryptanalysis**: Shor's algorithm factors RSA/breaks ECDH in polynomial time;
  Grover's algorithm halves effective key strength for AES/SHA brute force (p.3464).

### Code-breaking primitives (p.3469-3473)
- **Brute force**: exhaustive key search; cost table actually given in the module —
  | Budget | 40-bit | 56-bit | 64-bit | 128-bit |
  |---|---|---|---|---|
  | $2K (1 PC) | 1.4 min | 73 days | 50 years | 10^20 years |
  | $100K (company) | 2 sec | 35 hours | 1 year | 10^19 years |
  | $1M (state) | 0.2 sec | 3.5 hours | 37 days | 10^18 years |
  Rule of thumb used in the text: cracking DES-56 in 1s → AES-128 takes ~149 trillion years;
  every +1 key bit doubles the required time.
- **Frequency analysis**: letter/n-gram frequency in ciphertext (works great on classical ciphers
  and on encrypted **source code** specifically, since tokens like `#define`/`struct`/`return`
  repeat predictably — p.3469-3470).
- **Trickery/social engineering**: trick or bribe someone into encrypting a known message you
  can then use as a known-plaintext crib (p.3470).
- **Birthday attack** (hash collision search): need only `1.17·sqrt(2^n)` attempts to find a
  collision in an n-bit hash, not `2^n` — e.g. MD5 (128-bit) collision in ~2.2×10^19 tries instead
  of 3.4×10^38 (p.3472-3473). Directly relevant to forging signed messages with the same hash
  (**hash collision attack**, p.3482): find `a1`/`a2` with `hash(a1)=hash(a2)`, reuse a1's valid
  signature on the attacker-controlled a2.

## 3. Protocol / infrastructure attacks

- **Padding oracle attack** (Vaudenay attack, CBC mode, p.3487): if the server distinguishes
  "decryption failed: invalid padding" from a generic decryption error, that single bit of oracle
  feedback is enough to decrypt (and sometimes encrypt) arbitrary ciphertext without the key —
  byte-by-byte, abusing the CBC padding-removal step.
- **DROWN attack** (p.3484): cross-protocol Bleichenbacher-style padding-oracle attack — any
  server that still accepts SSLv2 (even on a different host sharing the same RSA cert) leaks enough
  to decrypt modern TLS sessions using that key. Check for: SSLv2 enabled anywhere a cert is
  reused.
- **DUHK (Don't Use Hard-coded Keys)** (p.3483): if a device uses the ANSI X9.31 RNG with a
  hard-coded seed, combining the known seed + observed current state lets an attacker rebuild
  the keystream and decrypt VPN/web traffic from that device.
- **Side-channel attacks** (p.3479-3481): exploit physical leakage instead of math —
  - Power analysis: **SPA** (direct trace reading) vs **DPA** (statistical, no algorithm knowledge
    needed).
  - EM field leakage, light/LED emission (CRT reconstruction, status-LED optical leakage),
    timing/delay variance, acoustic/keyboard emissions.
  - Mitigations worth knowing when auditing: constant-time crypto, masking/blinding with
    random nonces, noise injection, HSMs/secure enclaves.
- **Rainbow table attack** (p.3486): precomputed hash chains trade memory for time versus pure
  brute force — standard password-hash cracking method when salts are absent/weak.

## 4. Blockchain / DeFi attacks (attack playbooks, p.3489-3494)

- **51% attack**: control >50% of hash/stake power → mine a longer private chain in secret →
  release it to overwrite the public chain and reverse confirmed transactions (5-step playbook,
  p.3490-3491).
- **Finney attack**: pre-mine a block spending coin X to yourself (don't broadcast) → spend the
  same coin X with a merchant who accepts zero-confirmation → broadcast the pre-mined block
  immediately after they ship → merchant's tx is invalidated, you keep both the goods and the
  coin (p.3491-3492).
- **Race attack**: create two conflicting transactions off the same input, broadcast one to the
  victim (zero-conf accepted) and the other to the network, hope the self-paying one confirms
  first (p.3493-3494). No pre-mining needed, unlike Finney.
- **Eclipse attack**: flood a target node's peer table with attacker-controlled IPs, force a
  reconnect (e.g. via DoS), isolate the node behind only attacker peers, feed it a fake view of the
  chain (p.3492-3493).
- **DeFi sandwich attack**: watch the mempool for a large pending swap → front-run with a buy
  order to inflate price → let the victim's trade execute at the inflated price → immediately
  sell into the price spike you created (p.3494-3495). Classic MEV extraction pattern.

## 5. Quantum-era risk notes (p.3495-3496, for threat-modeling / CTF framing only)

Shor's algorithm breaks RSA/DSA/ECC factoring & discrete-log assumptions; Grover's algorithm
halves effective symmetric key strength. Practical implication called out explicitly: **harvest
now, decrypt later** — adversaries archive currently-unbreakable ciphertext today, planning to
decrypt it once quantum resources exist, which matters for anything needing long-term
confidentiality.

## 6. Tools

### Cryptanalysis / CTF-relevant
- **RsaCtfTool** (GitHub) — automates common weak-RSA attacks (small factors, common modulus,
  Wiener's attack, Fermat factorization, etc.) — the single most relevant tool here for CTF RSA
  challenges.
- **CrypTool** family (https://www.cryptool.org): CT1 (Windows, classic+modern algos, built-in
  cryptanalysis of Vigenère/RSA/AES), CT2 (visual pipeline GUI), JCrypTool (Linux/macOS/Windows,
  plugin-extensible), CrypTool-Online (browser).
- **Msieve** (SourceForge) — general number field sieve, factors large RSA-style moduli.
- **Cryptol**, **CryptoSMT**, **MTP** (all GitHub) — SMT-based/formal cryptanalysis tooling for
  symmetric primitives.
- **Online MD5/hash reversal lookups** (precomputed-table/dictionary lookups, fast first move
  before firing up hashcat): dcode.fr, md5decrypt.net, md5hashing.net, md5online.org,
  md5decrypter.com, onlinehashcrack.com, cmd5.org, hashes.com.

### Disk-encryption crackers / targets
- **hashcat** / **John the Ripper** — generic brute-force engines, see §1 for the VeraCrypt recipe
  (same shape for LUKS `-m 14600`-family modes, BitLocker `-m 22100`, TrueCrypt `-m 6211`-family
  — pick the mode matching the target, extract the header with `dd` first).
- **Cryptsetup** (Linux, `cryptsetup --help`) — manage/inspect dm-crypt, LUKS, loop-AES,
  TrueCrypt/VeraCrypt, and BitLocker-formatted volumes directly; `--disable-veracrypt` flag shows
  it natively understands VeraCrypt containers, useful for recon before cracking.

### General crypto toolkits (for building/testing payloads, not just defense)
- OpenSSL (`openssl` CLI) — X.509/CSR/CRL creation, raw symmetric/asymmetric primitive access.
- wolfSSL, Libsodium, Crypto++, PyCryptodome — library-level equivalents, useful when scripting
  an attack (padding-oracle automation, forging signatures, etc.) rather than shelling out.

## 7. Practical cheat-sheet for a CTF crypto box

1. Identify what you're facing: classical cipher (do frequency analysis first), block/stream cipher
   (check mode — CBC → think padding oracle; ECB → look for repeated blocks), RSA (check key
   size, look for small `e`, shared moduli, close primes → RsaCtfTool first), or a hash (check
   length → guess algo → try online reversal lookup before brute force).
2. If it's an encrypted container (VeraCrypt/LUKS/BitLocker/TrueCrypt): `dd` the header, pick the
   right `hashcat -m` mode, mask-attack short/numeric passwords before wordlist attacks.
3. If a padding-oracle-style error distinction is visible (different error for "bad padding" vs
   generic failure) on a CBC endpoint — that's a byte-by-byte decryption oracle, not just an info
   leak; automate with PyCryptodome/CrypTool rather than by hand.
4. If it's RSA with weird parameters (very small `e`, repeated modulus across multiple
   ciphertexts, primes close together) — RsaCtfTool before anything manual.
5. Don't forget the low-tech wins: dictionary/rainbow-table lookup on any raw hash before
   spinning up hashcat; trickery/known-plaintext crib if you can influence what gets encrypted.
