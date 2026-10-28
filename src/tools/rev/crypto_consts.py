#!/usr/bin/env python3
"""
Crypto Constant Finder — spot known algorithms in a binary by magic constants.

Scans raw bytes for well-known constants (hash IVs, S-box prefixes, CRC
tables, TEA delta, ...) in both little- and big-endian layouts and reports
file offsets.  Constants only: custom or constant-less algorithms (RC4, XOR
loops) will NOT be detected.

Usage:
    python3 crypto_consts.py ./binary
    python3 crypto_consts.py ./binary --json
"""

import argparse
import json
import re
import struct
import sys
from pathlib import Path
from typing import Dict, List

# name -> (kind, value).  "u32"/"u64" are searched in both endiannesses,
# "bytes" is searched as-is.
SIGNATURES = [
    ("MD5/SHA1 init (A)", "u32", 0x67452301),
    ("MD5/SHA1 init (B)", "u32", 0xEFCDAB89),
    ("SHA1 init (E)", "u32", 0xC3D2E1F0),
    ("SHA256 init (H0)", "u32", 0x6A09E667),
    ("SHA256 K[0]", "u32", 0x428A2F98),
    ("SHA512 init (H0)", "u64", 0x6A09E667F3BCC908),
    ("MD5 T[0]", "u32", 0xD76AA478),
    ("CRC32 poly (reflected)", "u32", 0xEDB88320),
    ("CRC32 table[1]", "u32", 0x77073096),
    ("AES Te0[0]", "u32", 0xC66363A5),
    ("Blowfish P-array[0]", "u32", 0x243F6A88),
    ("TEA/XTEA delta", "u32", 0x9E3779B9),
    ("FNV-32 offset basis", "u32", 0x811C9DC5),
    ("FNV-64 offset basis", "u64", 0xCBF29CE484222325),
    ("Mersenne Twister mult", "u32", 0x6C078965),
    ("Mersenne Twister mask", "u32", 0x9D2C5680),
    ("AES S-box", "bytes", bytes.fromhex("637c777bf26b6fc5")),
    ("AES inverse S-box", "bytes", bytes.fromhex("52096ad53036a538")),
    ("ChaCha/Salsa sigma", "bytes", b"expand 32-byte k"),
    ("ChaCha/Salsa tau", "bytes", b"expand 16-byte k"),
    ("Base64 alphabet", "bytes",
     b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"),
]

# Short single-constant hits are common by chance; only warn when relevant.
MAX_HITS_PER_SIG = 8


def _patterns(kind: str, value) -> Dict[str, bytes]:
    if kind == "bytes":
        return {"raw": value}
    fmt, bits = ("I", 32) if kind == "u32" else ("Q", 64)
    neg = (-value) & ((1 << bits) - 1)  # compilers turn `add K` into `sub -K`
    return {
        "LE": struct.pack("<" + fmt, value),
        "BE": struct.pack(">" + fmt, value),
        "LE-neg": struct.pack("<" + fmt, neg),
    }


def _find_all(data: bytes, needle: bytes, limit: int) -> List[int]:
    hits, start = [], 0
    while len(hits) < limit:
        idx = data.find(needle, start)
        if idx < 0:
            break
        hits.append(idx)
        start = idx + 1
    return hits


def scan(data: bytes) -> List[Dict[str, object]]:
    findings = []
    for name, kind, value in SIGNATURES:
        for layout, needle in _patterns(kind, value).items():
            offsets = _find_all(data, needle, MAX_HITS_PER_SIG)
            if offsets:
                findings.append({
                    "algorithm": name,
                    "layout": layout,
                    "offsets": [hex(o) for o in offsets],
                })
    return findings


DEFAULT_PREFIXES = "CTF|flag|FLAG|HTB|picoCTF|THM|DEADFACE"
MAX_XOR_SIZE = 32 * 1024 * 1024


def xor_flag_search(data: bytes, prefixes: str = DEFAULT_PREFIXES) -> List[Dict[str, object]]:
    """Try every single-byte XOR key over the whole file, look for flag-shaped text."""
    if len(data) > MAX_XOR_SIZE:
        return []
    flag_re = re.compile(rb"(?:" + prefixes.encode() + rb")\{[ -~]{4,60}\}")
    hits = []
    for key in range(1, 256):
        decoded = data.translate(bytes(b ^ key for b in range(256)))
        for m in flag_re.finditer(decoded):
            hits.append({
                "key": hex(key),
                "offset": hex(m.start()),
                "text": m.group().decode("ascii", "replace"),
            })
            if len(hits) >= 20:
                return hits
    return hits


def packed_warning(data: bytes) -> str:
    """Constants inside compressed/packed data are not visible: warn the user."""
    for marker, name in ((b"UPX!", "UPX"), (b"_MEIPASS", "PyInstaller")):
        if marker in data:
            return f"{name} marker present: unpack first, results below are unreliable"
    return ""


def main() -> int:
    parser = argparse.ArgumentParser(description="Find crypto constants in a binary")
    parser.add_argument("file", help="Target binary file")
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    parser.add_argument("--xor", action="store_true",
                        help="Also brute-force single-byte XOR for flag-shaped text")
    parser.add_argument("--prefixes", default=DEFAULT_PREFIXES,
                        help="Flag prefixes for --xor, regex alternation (default: %(default)s)")
    args = parser.parse_args()

    path = Path(args.file)
    if not path.is_file():
        print(f"[!] not a file: {path}", file=sys.stderr)
        return 1

    data = path.read_bytes()
    findings = scan(data)
    warning = packed_warning(data)
    xor_hits = xor_flag_search(data, args.prefixes) if args.xor else []
    if args.json:
        print(json.dumps({"warning": warning, "constants": findings,
                          "xor_flags": xor_hits}, indent=2))
        return 0

    if warning:
        print(f"[!] {warning}")
    for h in xor_hits:
        print(f"[FLAG?] xor key {h['key']} @ {h['offset']}: {h['text']}")

    if not findings and not xor_hits:
        print("[-] no known crypto constants (custom algo, XOR, or RC4-style?)")
        return 0
    for f in findings:
        print(f"[+] {f['algorithm']} ({f['layout']}) @ {', '.join(f['offsets'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
