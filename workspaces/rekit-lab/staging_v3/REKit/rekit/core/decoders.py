"""Opportunistic decoders for CTF-style layered encodings found in strings."""
from __future__ import annotations

import base64
import binascii
import codecs
import re
from typing import Any

FLAG_RE = re.compile(r"(?i)\b[a-z0-9_]{2,24}\{[^\r\n}]{3,160}\}")
B64_RE = re.compile(r"(?<![A-Za-z0-9+/=])[A-Za-z0-9+/]{16,}={0,2}(?![A-Za-z0-9+/=])")
HEX_RE = re.compile(r"(?<![0-9a-fA-F])(?:[0-9a-fA-F]{2}){8,}(?![0-9a-fA-F])")
MAGICS = {b"\x7fELF": "ELF", b"MZ": "PE", b"PK\x03\x04": "ZIP", b"\x1f\x8b": "GZIP", b"%PDF": "PDF", b"#!": "script"}


def _printable_ratio(b: bytes) -> float:
    return sum(1 for c in b if 32 <= c < 127 or c in (9, 10, 13)) / len(b) if b else 0.0


def _describe(raw: bytes) -> dict[str, Any] | None:
    magic = next((n for m, n in MAGICS.items() if raw.startswith(m)), None)
    ratio = _printable_ratio(raw)
    if magic is None and ratio < 0.85:
        return None
    text = raw.decode("latin-1")
    out: dict[str, Any] = {"preview": text[:120] if ratio >= 0.85 else raw[:16].hex(), "length": len(raw)}
    if magic:
        out["magic"] = magic
    flags = FLAG_RE.findall(text)
    if flags:
        out["flags"] = flags
    return out


def decode_candidates(strings: list[dict[str, Any]], limit: int = 100) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in strings:
        s = item["value"]
        for m in B64_RE.finditer(s):
            blob = m.group()
            if blob in seen or len(blob.rstrip("=")) % 4 == 1 or blob.isalpha() or blob.isdigit():
                continue
            seen.add(blob)
            try:
                raw = base64.b64decode(blob + "=" * (-len(blob) % 4), validate=True)
            except (binascii.Error, ValueError):
                continue
            d = _describe(raw)
            if d:
                results.append({"offset": item["offset"], "encoding": "base64", "source": blob[:80], **d})
        for m in HEX_RE.finditer(s):
            blob = m.group()
            if blob in seen:
                continue
            seen.add(blob)
            d = _describe(bytes.fromhex(blob))
            if d:
                results.append({"offset": item["offset"], "encoding": "hex", "source": blob[:80], **d})
        # reversed / rot13 flags
        for label, transformed in (("reversed", s[::-1]), ("rot13", codecs.encode(s, "rot_13"))):
            fl = FLAG_RE.findall(transformed)
            if fl and not FLAG_RE.findall(s):
                results.append({"offset": item["offset"], "encoding": label, "source": s[:80],
                                "preview": transformed[:120], "flags": fl, "length": len(s)})
        if len(results) >= limit:
            break
    return results
