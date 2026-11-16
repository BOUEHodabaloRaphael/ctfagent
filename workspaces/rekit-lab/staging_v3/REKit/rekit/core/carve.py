"""Embedded-file detection (droppers, appended payloads, firmware blobs)."""
from __future__ import annotations

import struct
import zlib
from typing import Any

from .binary import ParseError
from .pe import parse_pe


def _valid_pe(data: bytes, off: int) -> int | None:
    """Return the carved PE size if a well-formed PE header starts at ``off``."""
    if data[off:off + 2] != b"MZ" or off + 0x40 > len(data):
        return None
    lfanew = struct.unpack_from("<I", data, off + 0x3C)[0]
    if lfanew < 0x40 or lfanew > 0x1000 or data[off + lfanew:off + lfanew + 4] != b"PE\0\0":
        return None
    try:
        pb = parse_pe(data[off:])
    except (ParseError, struct.error):
        return None
    end = max([s.offset + s.size for s in pb.sections] + [0])
    return end or None


def carve(data: bytes, skip_first: bool = True, limit: int = 64) -> list[dict[str, Any]]:
    """Find embedded PE/ELF/ZIP/GZIP/RAR/7z/PDF/zlib streams. ``skip_first`` ignores offset 0."""
    found: list[dict[str, Any]] = []

    def add(off: int, kind: str, size: int | None, note: str = ""):
        if len(found) < limit and not (skip_first and off == 0):
            found.append({"offset": off, "type": kind, "size": size, "note": note})

    pos = 0
    while True:
        i = data.find(b"MZ", pos)
        if i < 0:
            break
        size = _valid_pe(data, i)
        if size:
            add(i, "PE", size)
        pos = i + 2
    pos = 0
    while True:
        i = data.find(b"\x7fELF", pos)
        if i < 0:
            break
        if i + 20 <= len(data) and data[i + 4] in (1, 2) and data[i + 5] in (1, 2) and data[i + 6] == 1:
            add(i, "ELF", None)
        pos = i + 4
    for magic, kind in ((b"PK\x03\x04", "ZIP"), (b"Rar!\x1a\x07", "RAR"), (b"7z\xbc\xaf\x27\x1c", "7-Zip"),
                        (b"%PDF-", "PDF"), (b"\x1f\x8b\x08", "GZIP"), (b"MSCF\0\0\0\0", "CAB")):
        pos = 0
        while len(found) < limit:
            i = data.find(magic, pos)
            if i < 0:
                break
            add(i, kind, None)
            pos = i + len(magic)
    for hdr in (b"\x78\x9c", b"\x78\xda", b"\x78\x01"):
        pos = 0
        while len(found) < limit:
            i = data.find(hdr, pos)
            if i < 0:
                break
            pos = i + 2
            try:
                d = zlib.decompressobj()
                out = d.decompress(data[i:i + 4_000_000], 1_000_000)
            except zlib.error:
                continue
            if len(out) >= 64 and d.eof is not None and (d.eof or len(out) >= 512):
                add(i, "zlib stream", len(data[i:i + 4_000_000]) - len(d.unused_data), f"inflates to >= {len(out)} bytes")
    return sorted(found, key=lambda x: x["offset"])
