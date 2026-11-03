# AFRICC CEH Slide Decks — Extracted Links

Source: 3 PPTX files in `/home/kali/Downloads/CEH/`:
- `AFRICC_Cryptography_Continued_24-09-2022.pptx` (crypto)
- `AFRICC_Linux_Fundentals_Part_2_updated_03-09-2022.pptx` (linux)
- `AFRICC_Python_Fundamentals_27-08-2022.pptx` (python)

Method: each `.pptx` was unzipped (it's a zip container) into an isolated scratchpad
subfolder per file, then `ppt/slides/*.xml` and `ppt/slides/_rels/*.xml.rels` were
grepped for `https?://...`. XML-namespace noise (`schemas.openxmlformats.org`,
`schemas.microsoft.com`) was filtered out as not real content links.

**Result: 30 raw URL occurrences → 28 unique URLs.** The Python deck contained
**no real hyperlinks** (only XML namespace URIs). All real links came from the
Crypto deck (26 unique) and the Linux deck (2 unique).

Note: web pages fetched below are untrusted third-party content — they were only
read and summarized, never treated as instructions.

## URLs by source file / slide

### AFRICC_Cryptography_Continued (crypto)

| Slide | URL |
|---|---|
| 3 | https://www.javatpoint.com/types-of-encoding-techniques |
| 3 | https://checkserp.com/encode/ascii/ |
| 3 | https://www.rapidtables.com/convert/number/ascii-hex-bin-dec-converter.html |
| 5 | https://quipqiup.com/ |
| 5 | https://www.base64decode.org/ |
| 5 | https://www.urldecoder.org/ |
| 5 | https://emn178.github.io/online-tools/base32_decode.html |
| 5 | https://cryptii.com/ |
| 5 | https://www.guballa.de/substitution-solver |
| 5 | https://www.guballa.de/vigenere-solver |
| 5 | https://rot13.com/ |
| 5 | https://www.dcode.fr/ |
| 5 | http://rumkin.com/tools/cipher/ |
| 5 | http://www.unit-conversion.info/texttools/morse-code/ |
| 5 | https://cryptii.com/pipes/ascii85-encoding |
| 6 | https://gchq.github.io/CyberChef/ |
| 6 | https://crackstation.net/ |
| 7 | https://www.youtube.com/watch?v=rVQpK6NcYIE |
| 7 | https://github.com/RsaCtfTool/RsaCtfTool |
| 10 | https://www.dcode.fr/frequency-analysis |
| 10 | https://crypto.interactive-maths.com/frequency-analysis-breaking-the-code.html |
| 11 | https://www.101computing.net/frequency-analysis/ |
| 12 | https://fareedfauzi.gitbook.io/ctf-checklist-for-beginner/ |
| 12 | https://charcharbinks.com/post/ctf_crypto_for_beginners/ |
| 13 | https://infosecwriteups.com/cryptography-essential-for-h4ck3r-and-ctf-player-0x1-encoding-b638ab5821a9 |
| 13 | https://d00mfist.gitbooks.io/ctf/content/ |

### AFRICC_Linux_Fundentals_Part_2 (linux)

| Slide | URL |
|---|---|
| 19 | https://www.linux.com/what-is-linux/ |
| 19 | https://linuxize.com/post/etc-shadow-file/ |

### AFRICC_Python_Fundamentals (python)

No real hyperlinks found. Only XML namespace URIs (`schemas.openxmlformats.org`,
`schemas.microsoft.com`) were present, which are OOXML format boilerplate, not
author-added links.

## Fetch status summary

28 unique URLs. **23 loaded successfully** (one of those, the YouTube page,
returned only page chrome/title, not the transcript; one, fareedfauzi's gitbook
page, 404'd but its sibling pages were inspected). **5 could not be loaded**
(persistent HTTP 403 from the site, or DNS resolution failure for javatpoint.com
from this environment) even after a retry: `base64decode.org`, `urldecoder.org`,
`infosecwriteups.com`, `linuxize.com`, `javatpoint.com`.

## Detailed summaries

### 1. http://rumkin.com/tools/cipher/
Rumkin.com's "pen and paper" cipher toolbox, all client-side. Three groups: (a)
~30 codes/substitutions — Base64, binary/hex/octal/decimal, Morse, Baudot,
Braille, Pigpen, Wingdings, T9, flag semaphore; (b) ~25 classical ciphers —
Caesar, Affine, Atbash, ROT13, Vigenère, Gronsfeld, Playfair, Bifid, Trifid,
ADFGX/ADFGVX, Quagmire I-IV, rail fence, columnar/double-columnar transposition,
Übchi, one-time pad; (c) analysis tools — letter-frequency counter, manual
cryptogram assistant, and an automated substitution-cipher solver.
**CTF use:** one-stop shop for the "is this Base64/hex/ROT13/Vigenère?" triage
step on unknown ciphertext, and the automated solver can crack monoalphabetic
substitutions outright. **Pentest use:** quick manual decode of obfuscated
strings found in configs/logs (not for anything cryptographically real).

### 2. https://charcharbinks.com/post/ctf_crypto_for_beginners/
2020 beginner's guide to CTF cryptography (motto: "Crypto? Never roll your
own"). Teaches the vocabulary (encoding vs cipher, plaintext/ciphertext, key,
frequency analysis, symmetric vs asymmetric) then walks through: encodings
(Base16/32/64 alphabets and padding tells, URL/percent-encoding, ASCII in
binary/octal/decimal/hex); symmetric substitution ciphers (Morse, letter
numbers, Caesar/ROT13, Baconian); polyalphabetic ciphers (Vigenère, Hill) that
resist naive frequency analysis; transposition ciphers (rail fence, columnar,
skip/nth-char). Recommends CyberChef, FeatherDuster, dCode, rumkin, Practical
Cryptography. **CTF use:** teaches pattern recognition for identifying an
unknown encoding/cipher by its visual "shape" (e.g., `=` padding + mixed
case/digits → Base64; all-uppercase/digits + `=` padding → Base32), which is
the single most useful skill for crypto-100-point challenges.

### 3. https://checkserp.com/encode/ascii/
A generic SEO-tool site's free ASCII encode/decode converter (text ↔ ASCII
codes), one of several encoders (Unicode, UTF-8, URL, HTML entities, Base64)
under the same "Tools" menu. **CTF use:** quick decode of ASCII-decimal/hex
hidden flags. **Pentest use:** crafting numeric-encoded payloads to test
input filters/WAFs. Caution: third-party site — don't paste real secrets into
it; prefer CyberChef or a local script for sensitive data.

### 4. https://crackstation.net/
Free online password-hash cracker using massive precomputed lookup tables
(~190GB/15B entries for MD5/SHA-1-class hashes, ~19GB/1.5B for others). Works
only on **unsalted** hashes; supports LM, NTLM, MD2/4/5, SHA-1/224/256/384/512,
RIPEMD-160, Whirlpool, MySQL 4.1+ (double SHA-1). Up to 20 hashes per request.
Also offers a downloadable ~1.49B-word wordlist and an open-source `preimage`
Rust CLI/library for offline/local lookups. **CTF/pentest use:** instant
recovery of weak/dictionary-based unsalted hashes (common in CTF crypto/misc
challenges and in dumped NTLM/MySQL hashes during an assessment); the
wordlist feeds hashcat/John for offline cracking when salted. Won't help
against bcrypt/Argon2/salted hashes.

### 5. https://cryptii.com/
Open-source (MIT), browser-side modular encoding/cipher/hash conversion tool
— all processing happens client-side, nothing sent to a server. Supports
chainable "pipes" such as hash functions, Caesar cipher, Enigma machine,
binary-to-text/English, and more (full catalog needs browsing the live app).
**CTF use:** fast multi-step decode/encode chaining for layered obfuscation
challenges; client-side execution is convenient when handling sensitive
challenge data without a third party seeing it.

### 6. https://cryptii.com/pipes/ascii85-encoding
The specific Cryptii "pipe" for Ascii85/Base85 — binary-to-text encoding
designed to carry arbitrary binary data over text-only channels. Encodes
text→Ascii85 and decodes Ascii85→text, fully client-side. **CTF use:**
peeling one layer of a multi-encoding chain when a string looks like Base85
(charset wider than Base64, often starts/ends with `<~`/`~>` in Adobe
variants). **Pentest use:** decoding Base85-encoded payloads/config values
found in logs or exploit traffic.

### 7. https://crypto.interactive-maths.com/frequency-analysis-breaking-the-code.html
Educational page on breaking substitution ciphers (monoalphabetic, Caesar
shift, Vatsyayana) via letter-frequency analysis. English letter frequency
facts: E, T, A, O most common; Z, Q, X rarest. Method: (1) count ciphertext
letter frequencies, (2) hypothesize frequent ciphertext letters map to
E/T/A/O, decrypt those, (3) use revealed word patterns to deduce remaining
letters. Warns short ciphertexts give unreliable statistics. Includes 8
practice cryptograms. **CTF use:** the manual fallback technique for
substitution-cipher challenges when no tool is available or the tool fails —
essential foundational skill, fails against polyalphabetic ciphers (Vigenère).

### 8. https://d00mfist.gitbooks.io/ctf/content/
A GitBook of CTF/pentest study notes (forked from xapax's security book),
organized by the typical pentest workflow: Basics (Linux/Windows/PowerShell/
Python/Git/file transfer/firewalls); Recon (subdomain enum, DNS/zone
transfers, email harvesting, Google dorking, tech-stack ID, port scanning);
Vulnerability analysis (LFI/RFI, path traversal, SQLi/NoSQLi, XXE, command
injection, upload-filter bypass, exposed VCS, XSS, CSRF, clickjacking, IDOR,
subdomain takeover); Exploitation (reverse/web shells, shellcode, Dirty COW,
Shellshock, Responder, log poisoning, buffer overflows); Post-exploitation
(Linux/Windows privesc, Meterpreter, restricted-shell escape, AV bypass,
credential looting, persistence, anti-forensics); Password cracking (custom
wordlists, hash ID, pass-the-hash); Pivoting/tunneling, traffic analysis
(ARP/DNS spoofing, SSL stripping, Wireshark), forensics, Wi-Fi (WEP/WPS), and
physical access. Author warns the notes/scripts are untested — verify before
use. **CTF use:** a broad phase-organized cheat sheet covering recon through
privesc, useful as a methodology checklist across almost any CTF category,
not just crypto.

### 9. https://emn178.github.io/online-tools/base32_decode.html
RFC 4648 Base32 decoder (handles padded/unpadded, case-insensitive by
default), with selectable output encoding (UTF-8, UTF-16, Hex, Base64, legacy
code pages). Explicitly states it only decodes, does not decrypt/verify.
**CTF use:** recovering flags/messages hidden in Base32 (common in multi-layer
encoding chains); switching output to Hex helps when the decoded bytes are
binary rather than text. **Pentest use:** decoding Base32 tokens/parameters
found in application data. Limitation: only the standard RFC 4648 alphabet —
non-standard Base32 variants won't decode correctly.

### 10. https://fareedfauzi.gitbook.io/ctf-checklist-for-beginner/
This exact page 404s (moved/renamed/deleted). From the GitBook's sibling pages
("CTF Training" by fareedfauzi) that are still listed, the resource appears
focused on **digital forensics for CTF beginners**: a general introduction,
a forensics-section introduction, and a "KAPE Triage" section with subpages
on Windows Registry Analysis and Event Log Analysis. **CTF use (inferred):**
likely a beginner checklist/workflow for Windows forensic-artifact triage
(KAPE-based collection + registry/event-log review), relevant to CTF forensics
categories rather than crypto specifically — the link in the crypto deck may
simply be stale or mis-filed.

### 11. https://gchq.github.io/CyberChef/
CyberChef ("The Cyber Swiss Army Knife"), GCHQ's browser-based data
analysis/decoding/encoding tool. Hundreds of chainable "operations" — Base64
decode, timestamp/timezone conversion, hexdump parsing, gzip decompression,
RC4 decrypt, x86 shellcode disassembly, SHA3 hashing, X.509 parsing, and more.
Operations chain into a shareable/reusable "recipe"; "Magic" auto-detects
encodings and suggests operations; "Fork" batch-processes many inputs with one
recipe. Runs entirely client-side (no server component) except three explicit
network-calling operations (Show on map, DNS-over-HTTPS, HTTP request); a
downloadable offline ZIP exists for air-gapped use. **CTF/pentest use:** the
single most versatile general-purpose tool for peeling multi-layer encodings,
decrypting known-key ciphers, parsing certs/shellcode, and prototyping data
transforms — a near-universal first stop for crypto/misc CTF challenges.

### 12. https://github.com/RsaCtfTool/RsaCtfTool
RsaCtfTool: open-source (MIT) Python CLI that automates attacks against weak
RSA keys/ciphertexts, built for education/CTF use. Implements: non-
factorization attacks (Wiener, Håstad broadcast, Boneh-Durfee, common-modulus,
small CRT exponent, partial p/q/d leaks, dp/dq leaks, Bellcore RSA-CRT fault
attack, lattice reduction); Coppersmith attacks (need optional SageMath) for
stereotyped messages, short padding, partial p/d recovery; factorization
methods (Fermat, Pollard rho/p-1, Williams p+1, ECM, SQUFOF, Quadratic Sieve,
Dixon, FactorDB lookup), plus ROCA-vulnerable-key detection and shared-factor
GCD checks across multiple keys; CTF-specific checks for known weird prime
forms, Z3, Wolfram Alpha. Usage: `--publickey key.pub --private`,
`--decryptfile`, `--attack <name>`, `--dumpkey`, `--isroca`; runs on Python
3.9+, also ships as Docker image. **CTF use:** the default go-to tool for RSA
crypto challenges — run it against the given public key/ciphertext and let it
try dozens of known weaknesses automatically instead of hand-coding each
attack. Limitation: only textbook semiprime moduli (no multiprime RSA); very
hard factorizations need external tools (msieve/yafu/cado-nfs).

### 13. https://infosecwriteups.com/cryptography-essential-for-h4ck3r-and-ctf-player-0x1-encoding-b638ab5821a9
Could not be loaded (persistent HTTP 403 from infosecwriteups.com / Medium,
even on retry). From the URL/title alone: appears to be part 1 ("0x1:
Encoding") of a Medium/InfoSec-Writeups series titled "Cryptography essential
for h4ck3r and CTF player," presumably covering basic encodings (Base64/hex/
URL encoding etc.) as groundwork before ciphers — consistent with its
placement in the deck next to the d00mfist CTF gitbook. Content not verified.

### 14. https://linuxize.com/post/etc-shadow-file/
Could not be loaded (persistent HTTP 403 from linuxize.com, even on retry).
From the URL/title and general knowledge: Linuxize's standard reference
article on the `/etc/shadow` file — explains its colon-separated fields
(username, hashed password, last-change date, min/max password age, warning
period, inactivity period, expiration date) and the `$id$salt$hash` crypt
format identifying the hash algorithm (`1`=MD5, `5`=SHA-256, `6`=SHA-512,
`y`/`2b` etc. for bcrypt/yescrypt depending on distro). Content not verified
by direct fetch. **CTF/pentest relevance (general knowledge):** `/etc/shadow`
is the canonical privilege-escalation/post-exploitation target on Linux —
reading it (via LFI, misconfigured permissions, or after root) yields hashes
to crack offline with hashcat/John, and the `$id$` prefix tells you which
hash mode to select.

### 15. https://quipqiup.com/
quipqiup, a free automated solver for cryptograms/cryptoquips (simple
substitution ciphers), by Edwin Olson. Handles "Cryptoquips" (word boundaries
kept) and "Patristocrats" (word boundaries removed, must also be recovered).
Lets you seed known letter/word mappings (e.g. `G=R`, `QVW=THE`) as clues and
offers alternate solving modes. **CTF use:** fast automated break of simple
substitution ciphers without manual frequency analysis; saves time versus
cipher 7/8 above. Doesn't help with transposition, Vigenère, or encodings
like Base64.

### 16. https://rot13.com/
Simple web utility offering ROT1 through ROT25 letter-shift ciphers (a
generalized Caesar shift), linked to an "About ROT13" explainer. **CTF use:**
ROT13 (shift 13, self-inverse since the alphabet has 26 letters) is a common
easy first-layer obfuscation in CTF challenges, often stacked with Base64;
trying all 25 shifts quickly is a standard check on any string that "looks
like scrambled English."

### 17. https://www.101computing.net/frequency-analysis/
Educational page on frequency analysis for breaking substitution ciphers
(monoalphabetic, Caesar, Vatsyayana), reiterating English letter-frequency
facts (E/T/A/O common, Z/Q/X rare) and the count → hypothesize → pattern-match
method, with a caveat about short-text unreliability. Ends with 8 practice
cryptograms (some pop-culture quotes). **CTF use:** same as entries 7 and —
teaching material/practice set for manual substitution-cipher breaking, a
core skill for crypto CTF categories.

### 18. https://www.base64decode.org/
Could not be loaded (persistent HTTP 403, even on retry). From the URL/title:
a standard free online Base64 encoder/decoder. **CTF/pentest relevance
(general knowledge):** Base64 is the single most common encoding layer found
in CTF flags, cookies, JWT segments, and web app parameters — a basic decoder
is a near-universal first step. Content not verified by direct fetch.

### 19. https://www.dcode.fr/
dCode: a large (900+ online tools) French site for "deciphering coded
messages, cheating at word games, solving puzzles, geocaches and treasure
hunts." Highlights: an AI-based cipher identifier claiming to recognize 250+
cipher types; Caesar, Vigenère, Polybius square and other classical ciphers;
codes/alphabets (Morse, A1Z26, leetspeak, Braille, symbol substitution,
barcode/QR generation); computing tools (ASCII, Base64, MD5, Unicode, binary,
BCD, Gray code, Brainfuck); math tools (equation/boolean solvers, prime
factorization, GCD, base conversion); data/image tools (regex search, text
diff, RGB channel split, ISBN lookup). **CTF use:** the cipher identifier is
an excellent first step on unknown ciphertext; the encoding/classical-cipher
tools cover most "layer 1" decode steps in multi-step crypto challenges.

### 20. https://www.dcode.fr/frequency-analysis
dCode's dedicated frequency-analysis tool: counts symbol frequency in
ciphertext with configurable normalization (letters-only/alphanumeric/all
chars, case/diacritic-insensitive, word-boundary handling) against reference
English/French/Spanish letter tables; supports single characters, bigrams,
trigrams, or arbitrary N-grams (overlapping or block mode); outputs
percentages/counts/missing-letters/longest-repeated-n-grams, can suggest a
likely alphabet mapping, and assesses substitution-vs-transposition
likelihood; exports CSV/TXT; links to an Index-of-Coincidence tool, bigram/
trigram tools, a monoalphabetic solver, and a cipher identifier. **CTF use:**
more rigorous/automatable version of the manual method in entries 7/17 —
useful for classifying an unknown cipher (substitution vs transposition vs
polyalphabetic) before picking an attack tool, and for confirming results on
longer ciphertexts where manual counting is impractical.

### 21. https://www.guballa.de/substitution-solver
guballa.de's Substitution Solver: breaks monoalphabetic substitution ciphers
("each letter of the clear text is replaced by a corresponding letter of the
cipher alphabet"). Paste ciphertext, pick a language (German, English,
Spanish, French, Dutch, Portuguese), click "Break Cipher." Algorithm isn't
described on the page; a Python implementation is linked on GitLab for those
wanting the method itself. **CTF use:** another automated substitution
solver (alternative to quipqiup/rumkin), useful when the plaintext language
isn't English or when quipqiup's assumptions don't fit.

### 22. https://www.guballa.de/vigenere-solver
guballa.de's Vigenère Solver: "breaks Vigenère ciphers without knowing the
key," supporting three variants (Classical Vigenère, Autokey Vigenère,
Beaufort), 6 languages, and a key-length parameter. Method undocumented on
page (linked to a German "Bits & Bytes" explainer). **CTF use:** directly
relevant tool for the common CTF scenario of polyalphabetic Vigenère
ciphertext with an unknown key — a key-space/frequency-based cryptanalysis
tool rather than brute force.

### 23. https://www.javatpoint.com/types-of-encoding-techniques
Could not be loaded (DNS resolution failure for javatpoint.com from this
environment, on two attempts). From the URL/title: a JavaTpoint tutorial
article enumerating encoding technique types (likely covering ASCII, Unicode,
Base64, URL encoding, HTML entity encoding, etc. as a general CS/web-dev
reference). **CTF/pentest relevance (general knowledge):** this kind of
survey article is background reading to recognize which encoding family a
challenge or web parameter is using. Content not verified by direct fetch.

### 24. https://www.rapidtables.com/convert/number/ascii-hex-bin-dec-converter.html
RapidTables' ASCII/Hex/Binary/Decimal/Base64 converter. Input accepts ASCII
text or hex/binary/decimal numbers; supports delimiters (none/space/comma/
custom), `0x`/`0b` prefix toggle, file input, byte-length display, and
checksums (8/16/32-bit sum, two's-complement, XOR). Includes a full ASCII
reference table and links to related hex-to-ASCII/binary-to-ASCII/Base64
tools. **CTF use:** quick multi-base decode of flags/data presented as
hex/binary/decimal strings, with the added checksum feature useful for
verifying/crafting data with a specific checksum.

### 25. https://www.urldecoder.org/
Could not be loaded (persistent HTTP 403, even on retry). From the URL/title:
a standard free online URL/percent-encoding encoder-decoder. **CTF/pentest
relevance (general knowledge):** URL/percent-encoding is routinely used to
obfuscate payloads in web parameters, cookies, and request bodies; decoding
is a basic step in both CTF web challenges and real request-tampering/WAF-
bypass testing. Content not verified by direct fetch.

### 26. https://www.youtube.com/watch?v=rVQpK6NcYIE
YouTube video titled **"How RSA Works."** The fetch only returned page
chrome (nav/footer links), not the description, channel, upload date, or
transcript, so exact content is unconfirmed. By title and its placement right
next to the RsaCtfTool GitHub link in the deck, it's almost certainly an
explainer of RSA key generation (large primes), encryption/decryption via
modular exponentiation, and why factoring the modulus breaks the scheme.
**CTF use:** conceptual prerequisite for understanding *why* RsaCtfTool's
attacks (Wiener, Håstad, Boneh-Durfee, Fermat, etc.) work, rather than a tool
itself.

### 27. http://www.unit-conversion.info/texttools/morse-code/
Morse code converter: text ↔ Morse code, in both directions. Explains dits
(dots)/dahs (dashes) encoding of Latin letters (plus some non-Latin
extensions), digits, and punctuation; mentions general uses (amateur radio,
aeronautical signaling, emergency SOS). **CTF use:** Morse code frequently
hides flags/strings in audio files, blinking-light/image patterns, or plain
text in CTF stego/crypto/misc challenges — this tool handles the final
text-level decode once the dots/dashes are extracted.

### 28. Combined note — the 5 unreachable pages
`https://www.base64decode.org/`, `https://www.urldecoder.org/`,
`https://infosecwriteups.com/...`, `https://linuxize.com/post/etc-shadow-file/`,
and `https://www.javatpoint.com/types-of-encoding-techniques` could not be
fetched (403 Forbidden from the site's bot protection, or DNS failure for
javatpoint.com), even after a retry. Their likely content is noted above
under each entry based on the URL/title and general knowledge only — this is
explicitly **not verified content** and should be treated as a weaker,
unconfirmed inference if it matters for later work.
