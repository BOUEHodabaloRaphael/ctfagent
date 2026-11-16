"""Single-byte XOR detection (CTF flags, obfuscated config tables, hidden payloads).

Key-independent search: for a plaintext marker ``m`` encrypted with one key ``k``, the XOR of
*neighbouring* bytes is the same as for the plaintext (``(m[i]^k)^(m[i+1]^k) == m[i]^m[i+1]``).
We therefore build the neighbour-XOR stream of the file once and search each marker's
difference pattern a single time, instead of decrypting the file 255 times. Every hit is then
verified by decoding a window around it. Scanning 8 MiB takes well under a second.
"""
from __future__ import annotations

import operator
import re
from typing import Any, Iterable

MARKERS: tuple[bytes, ...] = (
    b"This program cannot be run in DOS mode", b"/bin/busybox", b"/bin/sh", b"/bin/bash", b"/proc/",
    b"/dev/watchdog", b"/etc/passwd", b"cmd.exe", b"powershell", b"http://", b"https://",
    b"User-Agent", b"kernel32", b"LoadLibrary", b"GetProcAddress", b"HKEY_", b"password", b"Mozilla/",
    b"SOFTWARE\\", b"VirtualAlloc", b"WriteProcessMemory",
)
FLAG_PREFIXES: tuple[bytes, ...] = (b"flag{", b"FLAG{", b"CTF{", b"ctf{", b"HTB{", b"THM{", b"picoCTF{", b"DUCTF{")
MIN_PATTERN = 6  # shorter markers produce chance matches in multi-MiB buffers
_FLAG_BODY = re.compile(rb"[\x20-\x7e]{1,120}?\}")


def _table(key: int) -> bytes:
    return bytes(b ^ key for b in range(256))


def _diff_stream(buf: bytes) -> bytes:
    return bytes(map(operator.xor, buf, buf[1:]))


def _diff_pattern(m: bytes) -> bytes:
    return bytes(a ^ b for a, b in zip(m, m[1:]))


def _context(buf: bytes, pos: int, span: int = 80) -> str:
    end = pos
    while end < len(buf) and end - pos < span and 0x20 <= buf[end] < 0x7F:
        end += 1
    return buf[pos:end].decode("ascii", "replace")


def xor_scan(data: bytes, max_bytes: int = 16 * 1024 * 1024, extra: Iterable[bytes] = ()) -> list[dict[str, Any]]:
    """Return candidates sorted by evidence: ``[{key, key_hex, hits, markers, flags, offsets, samples}]``.

    ``extra`` adds known-plaintext markers (e.g. ``b"picoCTF{"`` or a hostname) of >= 6 bytes.
    """
    buf = data[:max_bytes]
    if len(buf) < MIN_PATTERN + 1:
        return []
    diff = _diff_stream(buf)
    per_key: dict[int, dict[str, Any]] = {}

    def record(key: int, name: str, pos: int, is_flag: bool = False, decoded: str = ""):
        rec = per_key.setdefault(key, {"key": key, "key_hex": f"0x{key:02x}", "hits": 0, "markers": {},
                                       "flags": [], "offsets": [], "samples": []})
        rec["hits"] += 1
        if is_flag:
            if decoded not in rec["flags"]:
                rec["flags"].append(decoded)
        else:
            rec["markers"][name] = rec["markers"].get(name, 0) + 1
        if len(rec["offsets"]) < 10:
            rec["offsets"].append(pos)
        if len(rec["samples"]) < 4:
            rec["samples"].append({"offset": pos, "text": decoded or _context(buf.translate(_table(key)), pos)})

    for marker in tuple(MARKERS) + tuple(extra) + FLAG_PREFIXES:
        if len(marker) < MIN_PATTERN - 1 and marker not in FLAG_PREFIXES:
            continue
        pat = _diff_pattern(marker)
        is_flag = marker in FLAG_PREFIXES
        start, seen = 0, 0
        while seen < 200:
            p = diff.find(pat, start)
            if p < 0:
                break
            start = p + 1
            key = buf[p] ^ marker[0]
            if key == 0:      # clear text, not an XOR
                continue
            if key == 0x20 and marker.isalpha():   # plain upper/lower-case flip, not obfuscation
                continue
            if not is_flag:   # flags are validated by their closing brace below
                window = buf[p:p + len(marker) + 8].translate(_table(key))
                tail = window[len(marker):]
                if tail and sum(1 for c in tail if 0x20 <= c < 0x7F or c == 0) < len(tail) * 0.75:
                    continue
            seen += 1
            if is_flag:
                dec = buf[p:p + len(marker) + 121].translate(_table(key))
                m = _FLAG_BODY.match(dec, len(marker))
                if m:
                    record(key, marker.decode(), p, True, dec[:m.end()].decode("ascii"))
            else:
                record(key, marker.decode("latin-1"), p)
    results = list(per_key.values())
    for r in results:
        r["offsets"] = sorted(set(r["offsets"]))
    return sorted(results, key=lambda r: -r["hits"])


def xor_decode(data: bytes, key: int, start: int = 0, end: int | None = None) -> bytes:
    return data[start:end].translate(_table(key))
