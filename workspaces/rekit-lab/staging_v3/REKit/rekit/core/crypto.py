"""Detection of cryptographic / hashing constants.

Constants are searched in little-endian, big-endian and two's-complement-negated form
(compilers often emit ``sub reg, 0x61c88647`` instead of ``add reg, 0x9e3779b9``).
A signature only fires when *enough* of its constants are present, and shared constants
(MD5/SHA-1 initial vectors) never identify an algorithm on their own.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass
from typing import Any

_AES_SBOX = bytes.fromhex("637c777bf26b6fc53001672bfed7ab76")
_AES_INV_SBOX = bytes.fromhex("52096ad53036a538bf40a39e81f3d7fb")


@dataclass(frozen=True)
class Sig:
    name: str
    kind: str                 # hash / cipher / checksum / prng / encoding / marker
    words: tuple[int, ...] = ()
    width: int = 4            # 4 or 8 bytes per constant
    need: int = 0             # minimum constants present (0 = all)
    blob: tuple[bytes, ...] = ()   # raw byte patterns (S-boxes, ASCII tables)
    confidence: str = "high"
    note: str = ""


SIGS: tuple[Sig, ...] = (
    Sig("MD5", "hash", (0xD76AA478, 0xE8C7B756, 0x242070DB, 0xC1BDCEEE), note="MD5 round constants T[1..4]"),
    Sig("SHA-1", "hash", (0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476, 0xC3D2E1F0), note="SHA-1 initial vector (needs H4=0xC3D2E1F0)"),
    Sig("SHA-1 round constants", "hash", (0x5A827999, 0x6ED9EBA1, 0x8F1BBCDC, 0xCA62C1D6), confidence="medium"),
    Sig("SHA-256 K table", "hash", (0x428A2F98, 0x71374491, 0xB5C0FBCF, 0xE9B5DBA5)),
    Sig("SHA-256 initial vector", "hash", (0x6A09E667, 0xBB67AE85, 0x3C6EF372, 0xA54FF53A), confidence="medium"),
    Sig("SHA-512 K table", "hash", (0x428A2F98D728AE22, 0x7137449123EF65CD), width=8),
    Sig("SHA-512 initial vector", "hash", (0x6A09E667F3BCC908, 0xBB67AE8584CAA73B), width=8, confidence="medium"),
    Sig("CRC-32 (IEEE) table", "checksum", (0x77073096, 0xEE0E612C, 0x990951BA, 0x076DC419), note="lookup table entries 1..4"),
    Sig("CRC-32 (IEEE) polynomial", "checksum", (0xEDB88320,), confidence="medium", note="bitwise CRC-32 implementation"),
    Sig("CRC-32C (Castagnoli) polynomial", "checksum", (0x82F63B78,), confidence="medium"),
    Sig("TEA / XTEA / XXTEA delta", "cipher", (0x9E3779B9,), confidence="medium", note="golden-ratio delta (also appears as 0x61C88647)"),
    Sig("Blowfish P-array", "cipher", (0x243F6A88, 0x85A308D3, 0x13198A2E, 0x03707344)),
    Sig("AES S-box", "cipher", blob=(_AES_SBOX,)),
    Sig("AES inverse S-box", "cipher", blob=(_AES_INV_SBOX,)),
    Sig("AES T-tables", "cipher", (0xC66363A5, 0xF87C7C84), confidence="high", note="Te0[0], Te0[1]"),
    Sig("ChaCha/Salsa20 sigma", "cipher", blob=(b"expand 32-byte k", b"expand 16-byte k")),
    Sig("FNV-1 / FNV-1a 32-bit", "hash", (0x811C9DC5, 0x01000193), confidence="medium"),
    Sig("MurmurHash3 (x86_32)", "hash", (0xCC9E2D51, 0x1B873593), confidence="medium"),
    Sig("Mersenne Twister MT19937", "prng", (0x6C078965, 0x9D2C5680, 0xEFC60000, 0x9908B0DF), need=3),
    Sig("Base64 alphabet", "encoding", blob=(b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/",)),
    Sig("Base64 alphabet (URL-safe)", "encoding", blob=(b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_",), confidence="medium"),
    Sig("Base32 alphabet", "encoding", blob=(b"ABCDEFGHIJKLMNOPQRSTUVWXYZ234567",), confidence="medium"),
    Sig("Magic marker", "marker", (0xDEADBEEF, 0xCAFEBABE, 0xBAADF00D, 0x8BADF00D, 0xFEEDFACE), need=1, confidence="low"),
)

_ENDIAN_FORMS = (("little", "<"), ("big", ">"))


def _forms(word: int, width: int) -> list[tuple[str, bytes]]:
    mask = (1 << (8 * width)) - 1
    out = []
    for label, e in _ENDIAN_FORMS:
        fmt = e + ("I" if width == 4 else "Q")
        out.append((label, struct.pack(fmt, word & mask)))
        out.append((label + ", negated", struct.pack(fmt, (-word) & mask)))
    return out


def find_all(data: bytes, needle: bytes, limit: int = 4) -> list[int]:
    hits, start = [], 0
    while len(hits) < limit:
        i = data.find(needle, start)
        if i < 0:
            break
        hits.append(i)
        start = i + 1
    return hits


def scan_crypto(data: bytes, max_scan: int = 32 * 1024 * 1024) -> list[dict[str, Any]]:
    """Return one record per detected algorithm: name, kind, confidence, offsets, evidence."""
    if len(data) > max_scan:
        data = data[:max_scan]
    cache: dict[bytes, list[int]] = {}

    def look(needle: bytes) -> list[int]:
        if needle not in cache:
            cache[needle] = find_all(data, needle)
        return cache[needle]

    results: list[dict[str, Any]] = []
    for sig in SIGS:
        evidence: list[dict[str, Any]] = []
        present = 0
        total = len(sig.words) + len(sig.blob)
        need = sig.need or total
        immediate = len(sig.words) <= 2 and sig.width == 4 and not sig.blob   # compilers may negate a lone immediate
        for n_done, w in enumerate(sig.words):
            if present + (len(sig.words) - n_done) + len(sig.blob) < need:
                break                                   # cannot reach the threshold any more: stop searching
            best = None
            for label, needle in _forms(w, sig.width):
                if label.endswith("negated") and not immediate:
                    continue
                hits = look(needle)
                if hits:
                    best = (label, hits)
                    break
            if best:
                present += 1
                evidence.append({"constant": f"0x{w:0{sig.width * 2}X}", "form": best[0],
                                 "offsets": [hex(o) for o in best[1]]})
        for b in sig.blob:
            hits = look(b)
            if hits:
                present += 1
                evidence.append({"pattern": b[:16].hex() if not b.isascii() else b.decode(), "form": "bytes",
                                 "offsets": [hex(o) for o in hits]})
        if present >= need and present > 0:
            results.append({"name": sig.name, "kind": sig.kind, "confidence": sig.confidence,
                            "matched": f"{present}/{total}", "note": sig.note, "evidence": evidence,
                            "first_offset": min(int(o, 16) for e in evidence for o in e["offsets"])})
    # MD5 / SHA-1 share an initial vector: report the ambiguity instead of guessing
    names = {r["name"] for r in results}
    if "MD5" not in names and "SHA-1" not in names:
        iv = tuple(_forms(0x67452301, 4))
        if any(look(n) for _, n in iv) and any(look(n) for _, n in _forms(0xEFCDAB89, 4)):
            results.append({"name": "MD4/MD5/SHA-1 family initial vector", "kind": "hash", "confidence": "low",
                            "matched": "2/4", "note": "shared initial values only; cannot tell which algorithm", "evidence": [],
                            "first_offset": look(_forms(0x67452301, 4)[0][1])[0] if look(_forms(0x67452301, 4)[0][1]) else 0})
    return results
