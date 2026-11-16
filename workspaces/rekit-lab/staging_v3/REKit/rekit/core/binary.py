"""Format-independent view of a parsed executable (ELF / PE / Mach-O).

All parsers are pure Python, bounds-checked and tolerant: malformed or hostile files
produce partial results plus ``warnings`` rather than exceptions.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass, field
from typing import Any, Optional


class ParseError(Exception):
    """Raised when a file cannot be interpreted as the requested format at all."""


def unpack(fmt: str, data: bytes, off: int):
    try:
        return struct.unpack_from(fmt, data, off)
    except struct.error as exc:  # truncated / out of range
        raise ParseError(f"truncated structure at 0x{off:x}") from exc


def cstr(data: bytes, off: int, maxlen: int = 1024) -> str:
    if off < 0 or off >= len(data):
        return ""
    end = data.find(b"\x00", off, off + maxlen)
    if end == -1:
        end = min(len(data), off + maxlen)
    return data[off:end].decode("latin-1")


@dataclass
class Section:
    name: str
    offset: int          # file offset of raw data
    size: int            # raw size in file (0 for NOBITS/.bss)
    vaddr: int           # virtual address (absolute, image base included for PE)
    vsize: int
    flags: str = ""      # e.g. "rwx", "r-x"
    kind: str = ""
    index: int = 0
    entropy: Optional[float] = None

    @property
    def executable(self) -> bool:
        return "x" in self.flags

    @property
    def writable(self) -> bool:
        return "w" in self.flags

    def has_offset(self, off: int) -> bool:
        return self.size > 0 and self.offset <= off < self.offset + self.size

    def has_vaddr(self, va: int) -> bool:
        return self.vsize > 0 and self.vaddr <= va < self.vaddr + self.vsize

    def to_dict(self) -> dict[str, Any]:
        return {"index": self.index, "name": self.name, "kind": self.kind,
                "offset": self.offset, "size": self.size, "vaddr": self.vaddr,
                "vsize": self.vsize, "flags": self.flags,
                "entropy": None if self.entropy is None else round(self.entropy, 4)}


@dataclass
class Segment:
    """A file-backed mapping used to translate virtual addresses to file offsets."""
    vaddr: int
    vsize: int
    offset: int
    size: int
    flags: str = ""
    name: str = ""


@dataclass
class Symbol:
    name: str
    value: int = 0
    size: int = 0
    kind: str = ""       # FUNC / OBJECT / NOTYPE ...
    bind: str = ""
    shndx: int = 0
    imported: bool = False
    lib: str = ""


@dataclass
class ParsedBinary:
    format: str                      # "ELF" | "PE" | "Mach-O"
    bits: int = 0
    endian: str = "little"
    arch: str = "unknown"            # normalised: x86 x86_64 arm aarch64 mips ppc ppc64 riscv ...
    machine: str = ""                # human-readable
    kind: str = ""                   # executable / shared object / dll / relocatable ...
    entry: Optional[int] = None      # virtual address
    image_base: int = 0
    sections: list[Section] = field(default_factory=list)
    segments: list[Segment] = field(default_factory=list)
    symbols: list[Symbol] = field(default_factory=list)
    imports: list[dict[str, Any]] = field(default_factory=list)
    exports: list[dict[str, Any]] = field(default_factory=list)
    protections: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    overlay: Optional[dict[str, int]] = None
    file_size: int = 0

    # ---- address translation -------------------------------------------------
    def vaddr_to_offset(self, va: int) -> Optional[int]:
        for seg in self.segments:
            if seg.size and seg.vaddr <= va < seg.vaddr + min(seg.size, seg.vsize or seg.size):
                return seg.offset + (va - seg.vaddr)
        return None

    def offset_to_vaddr(self, off: int) -> Optional[int]:
        for seg in self.segments:
            if seg.size and seg.offset <= off < seg.offset + seg.size:
                return seg.vaddr + (off - seg.offset)
        return None

    def section_for_offset(self, off: int) -> Optional[Section]:
        best = None
        for s in self.sections:
            if s.has_offset(off):
                if best is None or s.size < best.size:
                    best = s
        return best

    def section_for_vaddr(self, va: int) -> Optional[Section]:
        for s in self.sections:
            if s.has_vaddr(va):
                return s
        return None

    @property
    def entry_offset(self) -> Optional[int]:
        return None if self.entry is None else self.vaddr_to_offset(self.entry)

    def symbol_by_name(self, name: str) -> Optional[Symbol]:
        for s in self.symbols:
            if s.name == name and not s.imported and s.value:
                return s
        return None

    def symbol_at(self, va: int) -> Optional[Symbol]:
        best = None
        for s in self.symbols:
            if s.imported or s.kind not in ("FUNC", "GNU_IFUNC") or not s.value:
                continue
            if s.value <= va < s.value + max(s.size, 1):
                if best is None or s.value > best.value:
                    best = s
        return best

    def to_dict(self, max_symbols: int = 0) -> dict[str, Any]:
        out: dict[str, Any] = {
            "format": self.format, "bits": self.bits, "endian": self.endian,
            "arch": self.arch, "machine": self.machine, "kind": self.kind,
            "entry": self.entry, "image_base": self.image_base,
            "entry_offset": self.entry_offset,
            "sections": [s.to_dict() for s in self.sections],
            "imports": self.imports, "exports": self.exports,
            "symbol_count": len(self.symbols),
            "protections": self.protections, "metadata": self.metadata,
            "overlay": self.overlay, "warnings": self.warnings,
        }
        if max_symbols:
            out["symbols"] = [s.__dict__ for s in self.symbols[:max_symbols]]
        return out
