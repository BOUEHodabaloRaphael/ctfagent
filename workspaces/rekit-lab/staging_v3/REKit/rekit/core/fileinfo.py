from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any

from .macho import is_fat
from .util import entropy  # re-exported for backward compatibility

__all__ = ["MAGIC", "detect_type", "entropy", "inspect_file", "extract_strings", "DEFAULT_MAX_SIZE"]

DEFAULT_MAX_SIZE = 256 * 1024 * 1024

MAGIC = [
    (b"\x7fELF", "ELF"), (b"MZ", "PE/DOS"), (b"\xfe\xed\xfa\xce", "Mach-O 32-bit"),
    (b"\xce\xfa\xed\xfe", "Mach-O 32-bit"), (b"\xfe\xed\xfa\xcf", "Mach-O 64-bit"),
    (b"\xcf\xfa\xed\xfe", "Mach-O 64-bit"), (b"PK\x03\x04", "ZIP/JAR/APK"),
    (b"\x00asm", "WebAssembly"), (b"%PDF", "PDF"), (b"\x1f\x8b", "GZIP"), (b"BZh", "BZIP2"),
    (b"\xfd7zXZ\x00", "XZ"), (b"Rar!", "RAR"), (b"7z\xbc\xaf\x27\x1c", "7-Zip"),
    (b"SQLite format 3\x00", "SQLite"), (b"\x89PNG", "PNG"), (b"\xff\xd8\xff", "JPEG"),
    (b"GIF8", "GIF"), (b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1", "OLE2 (legacy Office/MSI)"),
    (b"{\\rtf", "RTF"), (b"dex\n", "Android DEX"), (b"L\x00\x00\x00\x01\x14\x02\x00", "Windows shortcut (LNK)"),
    (b"#!", "Script (shebang)"), (b"UPX!", "UPX stub"), (b"\x7fCGC", "DECREE CGC binary"),
    (b"\x1f\x9d", "compress (.Z)"), (b"MSCF", "Cabinet (CAB)"), (b"\x4d\x5a\x90\x00", "PE/DOS"),
]


def detect_type(data: bytes) -> str:
    if data[:4] == b"\xca\xfe\xba\xbe":
        return "Mach-O universal" if is_fat(data) else "Java class"
    for magic, name in MAGIC:
        if data.startswith(magic):
            return name
    if len(data) >= 262 and data[257:262] == b"ustar":
        return "TAR"
    return "Unknown/raw"


def inspect_file(path: str | Path, max_size: int = DEFAULT_MAX_SIZE) -> tuple[bytes, dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"File not found: {p}")
    if not p.is_file():
        raise ValueError(f"Target is not a regular file: {p}")
    size = p.stat().st_size
    if size > max_size:
        raise ValueError(f"File is {size} bytes, above the {max_size}-byte limit (use --max-size to raise it)")
    data = p.read_bytes()
    info: dict[str, Any] = {
        "name": p.name, "path": str(p.resolve()), "size_bytes": len(data),
        "md5": hashlib.md5(data, usedforsecurity=False).hexdigest(),
        "sha1": hashlib.sha1(data, usedforsecurity=False).hexdigest(),
        "sha256": hashlib.sha256(data).hexdigest(),
        "type": detect_type(data[:512]), "entropy": round(entropy(data), 5),
    }
    if data.startswith(b"\x7fELF") and len(data) >= 20:
        ei_class, ei_data = data[4], data[5]
        info["elf_class"] = {1: "ELF32", 2: "ELF64"}.get(ei_class, "unknown")
        info["endianness"] = {1: "little", 2: "big"}.get(ei_data, "unknown")
        machine = int.from_bytes(data[18:20], "little" if ei_data == 1 else "big") if ei_data in (1, 2) else -1
        info["elf_machine_id"] = machine
        info["elf_machine"] = {3: "x86", 40: "ARM", 62: "x86-64", 183: "AArch64", 8: "MIPS", 20: "PowerPC",
                               21: "PowerPC64", 243: "RISC-V"}.get(machine, "unknown")
    return data, info


_ASCII_CACHE: dict[int, re.Pattern] = {}


def extract_strings(data: bytes, min_length: int = 4, max_count: int = 50_000,
                    encodings: tuple[str, ...] = ("ascii", "utf-16le")) -> list[dict[str, Any]]:
    """Extract printable strings with file offsets.

    ``max_count`` is applied *per encoding* so that wide strings are never starved by a
    large number of ASCII strings (a bug in the v3.0 alpha).
    """
    if min_length < 1:
        raise ValueError("min_length must be >= 1")
    found: list[dict[str, Any]] = []
    if "ascii" in encodings:
        pat = re.compile(rb"[\x20-\x7e\t]{%d,}" % min_length)
        for i, m in enumerate(pat.finditer(data)):
            if i >= max_count:
                break
            found.append({"offset": m.start(), "encoding": "ascii", "value": m.group().decode("ascii")})
    if "utf-16le" in encodings:
        pat = re.compile(rb"(?:[\x20-\x7e\t]\x00){%d,}" % min_length)
        for i, m in enumerate(pat.finditer(data)):
            if i >= max_count:
                break
            found.append({"offset": m.start(), "encoding": "utf-16le", "value": m.group().decode("utf-16le")})
    if "utf-16be" in encodings:
        pat = re.compile(rb"(?:\x00[\x20-\x7e\t]){%d,}" % min_length)
        for i, m in enumerate(pat.finditer(data)):
            if i >= max_count:
                break
            found.append({"offset": m.start(), "encoding": "utf-16be", "value": m.group().decode("utf-16be")})
    return sorted(found, key=lambda x: x["offset"])
