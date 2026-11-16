"""Compare two files: byte ranges, sections, imports, strings, key metadata.

Useful to confirm exactly what a patch changed, or to compare malware variants / recompiles.
"""
from __future__ import annotations

import hashlib
from typing import Any

from .binary import ParsedBinary
from .fileinfo import extract_strings
from .formats import parse_binary


def byte_ranges(a: bytes, b: bytes, limit: int = 200) -> list[tuple[int, int]]:
    """Maximal runs where ``a`` and ``b`` differ (compared over the common length)."""
    n = min(len(a), len(b))
    if a[:n] == b[:n]:
        return []
    ranges: list[tuple[int, int]] = []
    i = 0
    while i < n and len(ranges) < limit:
        if a[i] == b[i]:
            # skip equal stretches quickly in 4 KiB hops
            while i + 4096 <= n and a[i:i + 4096] == b[i:i + 4096]:
                i += 4096
            while i < n and a[i] == b[i]:
                i += 1
            continue
        start = i
        while i < n and a[i] != b[i]:
            i += 1
        ranges.append((start, i))
    return ranges


def _sec_map(pb: ParsedBinary | None, data: bytes) -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    if pb:
        for s in pb.sections:
            blob = data[s.offset:s.offset + s.size]
            out[s.name] = {"size": s.size, "md5": hashlib.md5(blob, usedforsecurity=False).hexdigest(), "flags": s.flags}
    return out


def diff_files(a: bytes, b: bytes, max_strings: int = 200) -> dict[str, Any]:
    pa, _ = parse_binary(a)
    pb, _ = parse_binary(b)
    result: dict[str, Any] = {
        "identical": a == b,
        "size": {"a": len(a), "b": len(b)},
        "sha256": {"a": hashlib.sha256(a).hexdigest(), "b": hashlib.sha256(b).hexdigest()},
    }
    ranges = byte_ranges(a, b)
    result["byte_ranges"] = []
    for lo, hi in ranges:
        item: dict[str, Any] = {"offset": lo, "length": hi - lo, "a": a[lo:min(hi, lo + 16)].hex(), "b": b[lo:min(hi, lo + 16)].hex()}
        if pa:
            va = pa.offset_to_vaddr(lo)
            sec = pa.section_for_offset(lo)
            if va is not None:
                item["vaddr"] = va
            if sec:
                item["section"] = sec.name
        result["byte_ranges"].append(item)
    if len(a) != len(b):
        result["note"] = f"sizes differ ({len(a)} vs {len(b)}); byte ranges cover the common prefix only"
    sa, sb = _sec_map(pa, a), _sec_map(pb, b)
    result["sections"] = {
        "added": sorted(set(sb) - set(sa)), "removed": sorted(set(sa) - set(sb)),
        "changed": sorted(n for n in set(sa) & set(sb) if sa[n]["md5"] != sb[n]["md5"] or sa[n]["flags"] != sb[n]["flags"]),
    }
    ia = {f"{i.get('lib', '')}!{i.get('name') or i.get('ordinal')}" for i in (pa.imports if pa else [])}
    ib = {f"{i.get('lib', '')}!{i.get('name') or i.get('ordinal')}" for i in (pb.imports if pb else [])}
    result["imports"] = {"added": sorted(ib - ia)[:max_strings], "removed": sorted(ia - ib)[:max_strings]}
    sta = {x["value"] for x in extract_strings(a, 5)}
    stb = {x["value"] for x in extract_strings(b, 5)}
    result["strings"] = {"added": sorted(stb - sta)[:max_strings], "removed": sorted(sta - stb)[:max_strings],
                         "added_total": len(stb - sta), "removed_total": len(sta - stb)}
    meta: dict[str, Any] = {}
    if pa and pb:
        for key in ("imphash", "timestamp_utc", "pdb_path", "build_id"):
            va_, vb_ = pa.metadata.get(key), pb.metadata.get(key)
            if va_ != vb_:
                meta[key] = {"a": va_, "b": vb_}
        if pa.entry != pb.entry:
            meta["entry"] = {"a": pa.entry, "b": pb.entry}
    result["metadata"] = meta
    return result
