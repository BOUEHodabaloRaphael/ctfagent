# Changelog

## 3.1.0a1
### Added
- Pure-Python ELF, PE and Mach-O parsers (`core/elf.py`, `core/pe.py`, `core/macho.py`, `core/formats.py`).
- Commands: `strings`, `hexdump`, `find`, `disasm`, `xrefs`, `xor`, `carve`, `patch`, `unpack`, `diff`, `r2`, `ghidra`.
- Analyzers: crypto constants, single-byte XOR hunt, stack strings, decoders, embedded-file carving, packers,
  capabilities (ATT&CK hints), IOC noise filtering, imphash, `main()` recovery, x86 xref index.
- Safe patching: NOP / bytes / branch inversion for x86, ARM, Thumb, AArch64, MIPS with `EXPECT` checks.
- HTML report; colour console report; defanged indicators; `next_steps` and `attack` on findings.
- 67 new tests, a mutation fuzzer, and one regression test per bug in the v2.1 report.
### Changed
- Default `analyze` output is the console (was `both` files). Use `--format both` for the old behaviour.
- `--out` creates missing directories. `extract_strings` caps *per encoding*.
- `extract_iocs(include_noise=True)` is still the library default (v3.0 compatible); the profiles filter noise.
- Reports use schema version `"2"` (adds `summary`, `schema_version`, `Finding.next_steps`, `Finding.attack`).
### Fixed
- Canary / Fortify detection, per-section entropy, RC4 false alert, TEA / SHA-1 / MD5 confusion, stray `UPX!`,
  NUL bytes in IOCs, ARM entry point (see `tests/test_regressions_v21.py`).
- Duplicate xref reporting for REX-prefixed `lea`; objdump continuation lines for long instructions.
