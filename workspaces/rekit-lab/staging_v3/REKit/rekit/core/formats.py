"""Format detection and dispatch to the right parser."""
from __future__ import annotations

from .binary import ParsedBinary, ParseError
from .elf import parse_elf
from .macho import looks_macho, parse_macho
from .pe import parse_pe


def parse_binary(data: bytes) -> tuple[ParsedBinary | None, str | None]:
    """Return (parsed, error). ``parsed`` is None when the file is not a known executable."""
    try:
        if data[:4] == b"\x7fELF":
            return parse_elf(data), None
        if data[:2] == b"MZ":
            return parse_pe(data), None
        if looks_macho(data):
            return parse_macho(data), None
    except ParseError as exc:
        return None, str(exc)
    except (IndexError, ValueError, OverflowError, MemoryError) as exc:  # never crash on hostile input
        return None, f"parser failure: {type(exc).__name__}: {exc}"
    return None, None
