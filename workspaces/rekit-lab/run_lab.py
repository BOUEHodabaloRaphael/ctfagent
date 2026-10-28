#!/usr/bin/env python3
"""
REKit lab runner.

Runs vendor/REKITV2.py (downloaded, untrusted, run with `python3 -I` from work/)
against the samples built by build.sh and compares REKit's output with the
CORRECT behaviour.  FAIL means REKit deviates from ground truth.

Usage (from workspaces/rekit-lab/):
    ./build.sh && python3 run_lab.py
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
WORK = ROOT / "work"
REKIT = ROOT / "vendor" / "REKITV2.py"
OUT = ROOT / "results"
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def rekit(*args: str) -> str:
    proc = subprocess.run(
        [sys.executable, "-I", str(REKIT), *args],
        cwd=WORK, capture_output=True, text=True, timeout=120,
    )
    return ANSI.sub("", proc.stdout + proc.stderr)


# (id, sample, rekit args, regex, should_match, what the correct tool does)
CHECKS = [
    ("strings-flag", "plain", ["-s"], r"CTF\{plain_strcmp_flag\}", True,
     "finds a plaintext flag"),
    ("wide-flag", "wide", ["-s"], r"CTF\{wide_flag\}", True,
     "finds a UTF-16 flag"),
    ("packer-upx", "plain_upx", ["-packer"], r"Signature : UPX", True,
     "detects UPX"),
    ("packer-fp", "upxfake", ["-packer"], r"Signature : UPX", False,
     "does not call an unpacked binary UPX"),
    ("unpack-upx", "plain_upx", ["-unpack"], r"Unpacked :", True,
     "unpacks UPX"),
    ("rc4-tp", "rc4", ["-algo"], r"RC4", True,
     "flags RC4 on an RC4 binary"),
    ("rc4-fp-plain", "plain", ["-algo"], r"RC4", False,
     "does not flag RC4 on a strcmp binary"),
    ("rc4-fp-tea", "tea", ["-algo"], r"RC4", False,
     "does not flag RC4 on a TEA binary"),
    ("tea", "tea", ["-algo", "-c"], r"TEA", True,
     "detects TEA (delta 0x9e3779b9, stored as sub 0x61c88647)"),
    ("md5-only", "md5only", ["-algo"], r"SHA1", False,
     "MD5 IV alone is not reported as SHA1"),
    ("md5-tp", "md5only", ["-algo"], r"MD5", True,
     "reports MD5"),
    ("sha1-only", "sha1only", ["-algo"], r"MD5", False,
     "SHA1 IV is not reported as MD5 too"),
    ("md5-be", "md5_be", ["-algo", "-c"], r"MD5", True,
     "finds big-endian byte-array constants"),
    ("canary-only: canary", "canary_only", ["-p"], r"Canary : Oui", True,
     "canary detected"),
    ("canary-only: fortify", "canary_only", ["-p"], r"Fortify: Non", True,
     "Fortify must be No when only a canary is present"),
    ("fortify-only: fortify", "fortify_only", ["-p"], r"Fortify: Oui", True,
     "Fortify detected (__strcpy_chk)"),
    ("fortify-only: canary", "fortify_only", ["-p"], r"Canary : Non", True,
     "no canary"),
    ("nx-off", "nx_off", ["-p"], r"NX     : Non", True,
     "executable stack reported as NX off"),
    ("no-pie", "nopie_fullrelro", ["-p"], r"PIE    : Non", True,
     "-no-pie reported as PIE off"),
    ("full-relro", "nopie_fullrelro", ["-p"], r"RELRO  : Full", True,
     "Full RELRO"),
]


def main_addr(binary: Path) -> int:
    for line in subprocess.run(["nm", str(binary)], capture_output=True, text=True).stdout.splitlines():
        parts = line.split()
        if len(parts) == 3 and parts[2] == "main":
            return int(parts[0], 16)
    raise SystemExit("main not found")


def jump_after_strcmp(binary: Path) -> int:
    """File offset of the conditional jump that follows `call strcmp` in main."""
    dis = subprocess.run(["objdump", "-d", "-M", "intel", str(binary)],
                         capture_output=True, text=True).stdout
    seen = False
    for line in dis.splitlines():
        if "call" in line and "strcmp" in line:
            seen = True
        elif seen and re.search(r"\tj(e|ne|z|nz)\s", line):
            return int(line.split(":")[0].strip(), 16)
    raise SystemExit("jump not found")


def functional_checks(results):
    # Capstone default window should cover main
    m = main_addr(WORK / "crackme")
    out = rekit("crackme", "-cap")
    results.append(("cap-covers-main", f"-cap output contains main (0x{m:x})",
                    f"0x{m:08x}" in out))

    # -patch lists the conditional jump
    j = jump_after_strcmp(WORK / "crackme")
    out = rekit("crackme", "-patch")
    results.append(("patch-lists-jump", f"-patch lists the jump at 0x{j:x}",
                    f"0x{j:08x}" in out))

    # invert-jump really flips the check
    shutil.copy(WORK / "crackme", WORK / "crackme_patched")
    rekit("crackme_patched", "--invert-jump", hex(j))
    bad = subprocess.run([str(WORK / "crackme_patched")], input="wrong\n",
                         capture_output=True, text=True).stdout
    good = subprocess.run([str(WORK / "crackme_patched")], input="hunter2\n",
                          capture_output=True, text=True).stdout
    results.append(("invert-jump", "wrong password granted, right one denied",
                    "GRANTED" in bad and "DENIED" in good))

    # --nop makes the jump a no-op => falls through to the 'GRANTED' branch only if je/jne
    shutil.copy(WORK / "crackme", WORK / "crackme_nop")
    rekit("crackme_nop", "--nop", hex(j), "2")
    nop = subprocess.run([str(WORK / "crackme_nop")], input="wrong\n",
                         capture_output=True, text=True).stdout
    results.append(("nop-out", "nopped jump changes behaviour",
                    nop != subprocess.run([str(WORK / "crackme")], input="wrong\n",
                                          capture_output=True, text=True).stdout))


def main() -> int:
    if not (WORK / "plain").exists():
        print("run ./build.sh first", file=sys.stderr)
        return 1
    OUT.mkdir(exist_ok=True)
    rows = []
    for cid, sample, args, rx, should, what in CHECKS:
        out = rekit(sample, *args)
        (OUT / f"{cid.replace(' ', '_').replace(':', '')}.txt").write_text(out)
        matched = re.search(rx, out) is not None
        rows.append((cid, what, matched == should))
    functional_checks(rows)

    width = max(len(r[0]) for r in rows)
    failed = 0
    lines = ["| check | correct behaviour | result |", "|---|---|---|"]
    for cid, what, ok in rows:
        print(f"{'PASS' if ok else 'FAIL'}  {cid:<{width}}  {what}")
        lines.append(f"| {cid} | {what} | {'PASS' if ok else '**FAIL**'} |")
        failed += not ok
    (OUT / "summary.md").write_text("\n".join(lines) + "\n")
    print(f"\n{len(rows) - failed}/{len(rows)} pass, {failed} fail")
    return 0


if __name__ == "__main__":
    sys.exit(main())
