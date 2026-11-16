# REKit 3.1 alpha — CTF reverse engineering + malware static triage

REKit is a modular, **static-analysis** toolkit with two profiles (`ctf`, `malware`, or `both`) and a set of
stand-alone commands (disassemble, find xrefs, patch, XOR-decode, carve, diff…). It never executes the target.

> **Status: alpha.** Everything below was exercised against real gcc-built binaries, hand-built PE/Mach-O/ELF
> fixtures and a mutation fuzzer (see *Verification*). It is a triage and CTF aid, not a sandbox, not a
> decompiler and not a replacement for Ghidra / IDA / radare2.

## What is new in 3.1 (vs 3.0 alpha)

| Area | 3.0 alpha | 3.1 alpha |
|---|---|---|
| Format parsing | `readelf` subprocess, ELF only | **Pure-Python ELF / PE / Mach-O parsers** (no `readelf` needed), tolerant of malformed files |
| Protections | partial | NX / PIE / RELRO / canary / fortify / RWX / textrel for ELF; DEP / ASLR / CFG / SafeSEH-capable for PE |
| Imports | none | ELF dynsym (also recovered from the dynamic segment when section headers are stripped), PE import / delay-import / export tables, **imphash**, TLS callbacks, PDB path, Authenticode presence, .NET flag |
| Sections | none | Per-section entropy, flags, anomalies (RWX, entry point in last section, empty raw data…), overlay |
| Strings | ASCII + UTF-16LE | + UTF-16BE, per-encoding cap (no starvation), file offset **+ virtual address + section**, filters |
| IOCs | URL / IPv4 / email | + domains, registry keys, Windows/Unix paths, user-agents; **noise filtering** (private IPs, schema URLs); defanged in reports |
| Crypto constants | — | MD5, SHA-1/256/512, CRC32/32C, TEA, Blowfish, AES S-box/T-tables, ChaCha/Salsa, MT19937, FNV, Murmur, Base64/32 (LE, BE and negated forms) |
| Obfuscation | — | **Single-byte XOR hunt** (key-independent search, ~0.4 s for 8 MiB), base64 / hex / reversed / ROT13 decoding, **stack-string recovery** (x86/x86-64) |
| Packers | — | UPX / MPRESS / ASPack / Themida / VMProtect… with evidence, plus bundler/toolchain hints (PyInstaller, Go, Rust, .NET, AutoIt, NSIS…) and packing indicators |
| Capabilities | — | capa-style import + string mapping to behaviours with MITRE ATT&CK hints; severity rises only on strong combinations |
| CTF automation | strings only | `main()` recovery on stripped glibc binaries, **xrefs from "Correct/Wrong" strings to the validation function**, unsafe-libc and "win function" hints |
| Patching | — | NOP / byte patch / **branch inversion** (x86, ARM, Thumb, AArch64, MIPS), `EXPECT` byte check, dry-run, backup, post-write verification, PE checksum fix |
| Reports | JSON, Markdown | + **self-contained HTML** (dark mode, entropy bars), colour console; all output is escaped and indicators defanged |
| CLI | one command | 14 sub-commands; `rekit FILE` still works |
| Tests | 8 | 75 (74 pass, 1 skipped: see below) |

## Install

```bash
cd REKit
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -e '.[dev]'
# optional extras
python -m pip install -e '.[capstone]'   # multi-architecture disassembly
python -m pip install -e '.[yara]'       # YARA rule scanning
```

No dependency is required for analysis. `objdump` (binutils) is used for `disasm` when Capstone is absent;
`upx` is needed by `unpack`; `r2` / `analyzeHeadless` by the optional bridges.

## Commands

```text
rekit analyze FILE      full triage (default; `rekit FILE` is shorthand)
rekit strings FILE      strings with offset / virtual address / section, regex and IOC filters
rekit hexdump FILE      hex dump at --at / --va / --symbol / --main / --entry
rekit find FILE         bytes with ?? wildcards, text (ASCII + UTF-16), regex
rekit disasm FILE       Capstone (or objdump) from --va / --symbol / --main / --entry
rekit xrefs FILE        code that references a string / address / symbol (x86, x86-64)
rekit xor FILE          single-byte XOR scan; --key K --dump out.bin to decode
rekit carve FILE        locate and --extract embedded PE/ELF/ZIP/zlib/...
rekit patch FILE        --bytes / --nop / --invert, with --expect safety, --dry-run, --in-place
rekit unpack FILE       UPX unpacking (needs `upx`)
rekit diff A B          byte ranges (with virtual address and section), imports, strings, metadata
rekit r2 FILE           radare2 summary (needs r2; run malware only in an isolated VM)
rekit ghidra FILE       Ghidra headless decompilation (needs analyzeHeadless; isolated VM)
```

Analyze options: `--profile ctf|malware|both`, `--format console,json,markdown,html,both,all`, `--out PATH`
(directories are created), `--yara-rules FILE|DIR`, `--no-xor`, `--no-carve`, `--no-leads`, `--include-noise`,
`--no-defang`, `--max-size BYTES`, `-v`.

### Workflow 1 — CTF crackme (verified end to end on a gcc-built sample)

```bash
rekit ./crackme --profile ctf
#  [MEDIUM] Code that references success/failure/flag strings (CTF-LEAD-001)
#      'Wrong password' <- lea @0x10d4 in sub_10a0 (0x10a0)
#      → rekit disasm <file> --va 0x10a0 -n 80

rekit disasm ./crackme --main -n 60              # read the validation code
rekit xrefs  ./crackme --string "Correct password"
rekit patch  ./crackme --va --invert 0x4011b4 --out crackme.patched   # je -> jne, EXPECT-checked
rekit diff   ./crackme ./crackme.patched         # exactly one byte, in .text
```

### Workflow 2 — malware triage (static only)

```bash
rekit ./sample.exe --profile malware --format html,json --out reports/sample
```

The report contains per-section entropy, imports grouped by DLL, imphash, packer evidence, behavioural
capabilities with ATT&CK hints, noise-filtered IOCs (defanged), embedded payloads, XOR-obfuscated content and
suggested next commands. **There is deliberately no benign/malicious verdict.**

## v2.1 migration

| v2.1 flag | v3.1 |
|---|---|
| `-a` | `rekit analyze FILE` |
| `-i`, `-e`, `-p` | `rekit analyze` (structure + protections) |
| `-s` | `rekit strings FILE` |
| `-d`, `-cap` | `rekit disasm FILE` |
| `-io` | `rekit analyze` / `rekit strings --iocs` |
| `-r`, `-o` | `rekit find --regex/--text` |
| `-x`, `-l` | `rekit hexdump FILE --at OFF -n LEN` |
| `-c`, `-algo` | `rekit analyze` (crypto constants) |
| `-r2`, `-gh` | `rekit r2`, `rekit ghidra` |
| `-packer`, `-unpack` | `rekit analyze`, `rekit unpack` |
| `-patch`, `--patch-bytes`, `--nop`, `--invert-jump` | `rekit patch --bytes / --nop / --invert` |

The v2.1 test-report bugs are each covered by a regression test (`tests/test_regressions_v21.py` and the tests
named there): canary on stripped binaries, RC4 false alert (removed), Fortify false positive, per-section entropy,
TEA / big-endian / negated constants, SHA-1 vs MD5, stray `UPX!`, NUL in IOCs, ARM / entry-point start.

## Verification — what was and was not tested

**Verified in this build**

* 74 automated tests pass, including every bug of the v2.1 report; the 8 original v3.0 tests still pass unchanged.
* ELF parser cross-checked against `readelf` (protections, section offsets, sizes, entropy) on gcc binaries
  (PIE / non-PIE / full RELRO / canary / fortify / stripped).
* `main()` recovery on stripped PIE and non-PIE binaries equals the symbol-table truth; the string → function
  xref lands on `main`.
* A patched crackme was **executed**: it accepts a wrong password and rejects the right one; every safety check
  (wrong `EXPECT`, non-branch byte, out-of-range) refuses.
* Parsers and the whole engine survived over 2,000 random mutations / truncations of PE, ELF and Mach-O inputs
  (795 of them run inside the test-suite with fixed seeds).
* Reports: HTML/Markdown escape hostile strings (`<script>`, backticks, markdown tables) and defang URLs.
* Measured in the build sandbox (your hardware will differ), `--profile both`: `/bin/ls` 0.1 s, 8 MB `python3` 4.0 s,
  125 MB of random data 16.6 s. An early draft of the XOR scan that decrypted the file 255 times needed 53 s on that
  8 MB binary; the current key-independent search takes 0.4 s.

**Not verified here (no tool / sample available) — treat with caution**

* **Capstone path**: not installed in the build sandbox. The mapping code is written but untested; the objdump
  fallback is tested on x86-64 only. The ARM disassembly test is skipped here (x86-only `objdump`).
* **ARM / Thumb / AArch64 / MIPS branch inversion** is unit-tested on hand-encoded instructions, not on real
  binaries; x86 inversion is verified on a real executable.
* **PE and Mach-O** parsers are tested on hand-built fixtures and fuzzing, **not on real Windows/macOS
  binaries** (none were available offline). Please run them on a few real samples before relying on them.
* `unpack` (needs `upx`), **YARA** scanning, and the **radare2 / Ghidra** bridges were tested with stub
  executables only: invocation and parsing are checked, the behaviour of the real tools is not.
* The Mirai sample from the v2.1 report was not available; its *shape* (static ARM ELF, no section headers, no
  `PT_GNU_STACK`) is covered by a synthetic regression test.

## Limits worth knowing

* x86 / x86-64 only for xrefs, stack strings and `main` recovery; other architectures use headers, symbols, strings.
* XOR search covers a single repeating byte (not multi-byte keys). Stack-string recovery covers `mov` immediates,
  not SSE/AVX-built strings.
* Crypto-constant search reads the first 32 MiB and the XOR scan the first 16 MiB of very large files (reported).
* Capability and packer findings are indicators; benign software triggers many of them.

## Development

```bash
python -m pytest            # or: python -m unittest discover -s tests   (tests need gcc for some cases; they skip cleanly)
python -m compileall -q rekit tests
```

## Safety

Analyse only files you are authorised to examine, in an isolated lab. REKit never executes samples, but the
optional radare2 / Ghidra bridges parse untrusted input in external tools that have had parser vulnerabilities:
use them on malware only inside a disposable VM or container without network access.
