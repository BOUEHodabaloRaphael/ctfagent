# REKit v2.1 lab report

Target: `Reverse/Version2/REKITV2.py` from emerick-19/Tools (sha256 in `vendor/SHA256`).
Reproduce: `./build.sh && python3 run_lab.py` (results in `results/`).
Ground truth comes from how each sample was compiled. 24 checks: 15 pass, 9 fail.

## Failures (REKit deviates from ground truth)

| id | what happens |
|---|---|
| rc4-fp-plain / rc4-fp-tea | "RC4/XOR loop probable" fires on every binary (counts `ff 00 00 00`). The rc4-tp pass is meaningless. |
| tea | No TEA signature; only little-endian positive constants are searched, gcc emits `sub 0x61c88647`. |
| md5-only / sha1-only | MD5 IV alone is reported as SHA1 (4/5) and SHA1 IV as MD5 (4/4): shared constants, 60 % threshold. |
| md5-be | Big-endian byte-array constants are missed. |
| canary-only: fortify | `"_chk"` matches `__stack_chk_fail`: canary without Fortify prints `Fortify: Oui`. |
| packer-fp | The string `UPX!` in a normal binary is reported as a UPX signature. |
| cap-covers-main | `-cap` starts at fixed 0x1000 and prints 60 instructions: stops at 0x10e4, main is at 0x1159. |

## Pass
Plaintext and UTF-16 flag strings, UPX detection and `-unpack`, NX off, no-PIE, Full RELRO,
Fortify (when really present), `-patch` listing, `--invert-jump`, `--nop`.

## Fix ideas
1. Drop the `ff 00 00 00` RC4 heuristic.
2. Fortify: match `__\w+_chk` excluding `__stack_chk`.
3. Search each constant as LE, BE and negated; add TEA delta.
4. Make SHA1 require `0xc3d2e1f0`.
5. Packer: check the magic at the expected place (UPX! near ELF/PE headers), not anywhere.
6. Capstone: start at `e_entry` or at `main` from the symbol table.

## Real CTF binaries (workspaces of this repo, 9 ELF: x86-64, MIPS, PowerPC, aarch64)

Compared `-p -algo -c -packer` with `readelf` ground truth.

| finding | evidence |
|---|---|
| Canary missed on dynamic binaries | pwn002 `vault`, pwn-004 `pets`, kbxac `sheetforge` all import `__stack_chk_fail`, REKit says `Canary: Non`. Cause: `readelf -s` without `-W` truncates versioned names to `__[...]@GLIBC_2.4`. Same truncation hurts the dangerous-symbols list in `-e`. |
| Fortify false positive | pwn001 `vault`: canary only, 0 real `__*_chk`, REKit says `Fortify: Oui`. |
| RC4 alert noise | Fires on 5 of 9 real binaries. |
| Crypto hits plausible | kbxac `chall`: CRC32 + MD5 + SHA1 (5/5) + SHA256, consistent with a hashing challenge. |
| Not multi-arch | `-cap` always uses x86 mode for ELF: empty output on aarch64. checksec and constants still run on MIPS/PPC (big-endian constants are missed). |

## Sandbox run on malware-like samples (docker, static only)

`sandbox/run.sh <sample> [REKit args]`: image `rekit-sandbox`, `--network none`, read-only root,
`--cap-drop ALL`, no-new-privileges, non-root, 128 pids / 512 MB / 1 CPU, sample and REKit mounted `:ro`.
Isolation checked: outbound connect fails (`Network is unreachable`), writes fail (`Read-only file system`).
Samples are benign stand-ins (`samples/`): `fake_dropper` (C2 URL, IP, email, Run key, drop path, XOR-ed config),
a UPX-packed copy, and the EICAR test string. No real malware was downloaded or executed.

| finding | evidence |
|---|---|
| IOC extraction works | URL, IP, email, Run key and drop path all found in `fake_dropper`. |
| Registry/path IOCs run on into following bytes | Regex `[^\s"']+` does not stop at NUL: `...\Run\Updater C:\Users\...exe 2..*`uukj...` (garbage appended). |
| Per-section entropy is wrong | `-packer` regex takes the address/offset columns as offset/size: `.note.gnu.build-id taille=848` (0x350 = file offset) while the real size is 0x24. Entropy is computed on the wrong bytes, so the packer-by-entropy hint is unreliable. |
| Packed samples give corrupted IOCs | UPX copy: `http://185.220.10¿;ûÿ1.45/gate.php`. Unpack first (`-unpack`). |
| XOR-ed config not decoded | Expected: not a REKit feature. |
| EICAR not recognised | Expected: no AV signatures. |
| RC4 alert fires again | Same noise as before. |
