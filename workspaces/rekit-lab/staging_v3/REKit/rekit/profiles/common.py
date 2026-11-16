"""Helpers shared by the analysis profiles."""
from __future__ import annotations

from typing import Any

from ..core.binary import ParsedBinary
from ..core.models import Finding


def where(pb: ParsedBinary | None, offset: int) -> str:
    """Human-readable location: ``0x2010 (.rodata, va 0x402010)``."""
    parts = []
    if pb is not None:
        sec = pb.section_for_offset(offset)
        va = pb.offset_to_vaddr(offset)
        if sec:
            parts.append(sec.name)
        if va is not None:
            parts.append(f"va 0x{va:x}")
    return f"0x{offset:x}" + (f" ({', '.join(parts)})" if parts else "")


def opt(options: dict[str, Any] | None, key: str, default: Any) -> Any:
    return default if not options or key not in options else options[key]


def protections_lines(pb: ParsedBinary) -> list[str]:
    p = pb.protections
    if pb.format == "ELF":
        keys = ("nx", "pie", "relro", "canary", "fortify")
        lines = [f"{k.upper():8}: {p.get(k, 'unknown')}" for k in keys]
        lines.append(f"{'STRIPPED':8}: {'yes' if p.get('stripped') else 'no'}   {'STATIC' if p.get('static') else 'DYNAMIC'}")
        if p.get("rwx_segments"):
            lines.append(f"RWX segments: {p['rwx_segments']}")
        return lines
    if pb.format == "PE":
        return [f"{k.upper():16}: {'yes' if v else 'no'}" for k, v in p.items() if isinstance(v, bool)] + \
               [f"RWX sections: {p.get('rwx_sections', 0)}"]
    return [f"{k}: {v}" for k, v in p.items()]


def cached(options: dict[str, Any] | None, key: str, fn):
    """Memoise expensive scans (xor/carve/crypto) so ``--profile both`` computes each only once."""
    if options is None:
        return fn()
    cache = options.setdefault("_cache", {})
    if key not in cache:
        cache[key] = fn()
    return cache[key]
