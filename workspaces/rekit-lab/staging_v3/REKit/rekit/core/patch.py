"""Safe binary patching for CTF crackmes and analysis: byte patches, NOP-out, branch inversion.

Safety properties: patches go to a *copy* by default, original bytes can be asserted with
``expect`` (refuse to patch the wrong place), a dry-run mode previews every change, in-place
edits keep a ``.bak`` backup, and the result is re-read and verified after writing.
"""
from __future__ import annotations

import shutil
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from .binary import ParsedBinary
from .pe import pe_checksum

X86_JCC = {0x70: "jo", 0x71: "jno", 0x72: "jb", 0x73: "jae", 0x74: "je", 0x75: "jne", 0x76: "jbe", 0x77: "ja",
           0x78: "js", 0x79: "jns", 0x7A: "jp", 0x7B: "jnp", 0x7C: "jl", 0x7D: "jge", 0x7E: "jle", 0x7F: "jg"}
ARM_COND = ["eq", "ne", "cs", "cc", "mi", "pl", "vs", "vc", "hi", "ls", "ge", "lt", "gt", "le", "al", "nv"]


class PatchError(Exception):
    pass


@dataclass
class PatchOp:
    offset: int
    new: bytes
    expect: Optional[bytes] = None
    description: str = ""


def parse_hex(text: str) -> bytes:
    cleaned = text.replace("0x", "").replace(" ", "").replace(",", "").replace(":", "")
    try:
        return bytes.fromhex(cleaned)
    except ValueError as exc:
        raise PatchError(f"invalid hex string: {text!r}") from exc


def nop_bytes(arch: str, length: int, endian: str = "little", mode: str | None = None) -> bytes:
    if length <= 0:
        raise PatchError("NOP length must be positive")
    if arch in ("x86", "x86_64"):
        return b"\x90" * length
    unit = {"arm": b"\x00\x00\xa0\xe1", "aarch64": b"\x1f\x20\x03\xd5", "mips": b"\x00\x00\x00\x00",
            "mips64": b"\x00\x00\x00\x00", "ppc": b"\x60\x00\x00\x00", "ppc64": b"\x60\x00\x00\x00",
            "riscv": b"\x13\x00\x00\x00"}.get(arch)
    if arch == "arm" and mode == "thumb":
        if length % 2:
            raise PatchError("Thumb NOP patches must be a multiple of 2 bytes")
        return b"\x00\xbf" * (length // 2)
    if unit is None:
        raise PatchError(f"no NOP encoding known for architecture {arch!r}")
    if length % 4:
        raise PatchError(f"{arch} NOP patches must be a multiple of 4 bytes")
    if endian == "big" and arch in ("arm", "aarch64", "riscv"):
        unit = unit[::-1]
    return unit * (length // 4)


def invert_branch(data: bytes, off: int, arch: str, endian: str = "little", mode: str | None = None) -> tuple[bytes, bytes, str]:
    """Return (old_bytes, new_bytes, description) for the conditional branch at ``off``."""
    if off < 0 or off >= len(data):
        raise PatchError("offset outside the file")
    if arch in ("x86", "x86_64"):
        op = data[off]
        if op in X86_JCC:
            return data[off:off + 1], bytes([op ^ 1]), f"{X86_JCC[op]} -> {X86_JCC[op ^ 1]} (short)"
        if op == 0x0F and off + 1 < len(data) and 0x80 <= data[off + 1] <= 0x8F:
            o2 = data[off + 1]
            return data[off:off + 2], bytes([0x0F, o2 ^ 1]), f"{X86_JCC[o2 - 0x10]} -> {X86_JCC[(o2 ^ 1) - 0x10]} (near)"
        raise PatchError(f"byte 0x{op:02x} at 0x{off:x} is not a conditional jump opcode (expected 70-7F or 0F 80-8F)")
    e = "<" if endian == "little" else ">"
    if arch == "arm" and mode == "thumb":
        (hw,) = struct.unpack_from(e + "H", data, off)
        cond = (hw >> 8) & 0xF
        if hw >> 12 == 0xD and cond < 0xE:
            new = (hw & 0xF0FF) | ((cond ^ 1) << 8)
            return data[off:off + 2], struct.pack(e + "H", new), f"b{ARM_COND[cond]} -> b{ARM_COND[cond ^ 1]} (thumb)"
        raise PatchError("not a Thumb conditional branch (expected 0xD0xx-0xDDxx)")
    if arch in ("arm", "aarch64", "mips", "mips64", "riscv") and off + 4 > len(data):
        raise PatchError("truncated instruction")
    if arch == "arm":
        (w,) = struct.unpack_from(e + "I", data, off)
        cond = w >> 28
        if (w >> 25) & 7 == 0b101 and cond < 0xE:
            return data[off:off + 4], struct.pack(e + "I", w ^ 0x10000000), f"b{ARM_COND[cond]} -> b{ARM_COND[cond ^ 1]}"
        raise PatchError("not a conditional ARM branch (condition AL branches cannot be inverted)")
    if arch == "aarch64":
        (w,) = struct.unpack_from(e + "I", data, off)
        if (w & 0xFF000010) == 0x54000000 and (w & 0xF) < 0xE:
            c = w & 0xF
            return data[off:off + 4], struct.pack(e + "I", w ^ 1), f"b.{ARM_COND[c]} -> b.{ARM_COND[c ^ 1]}"
        if (w & 0x7E000000) in (0x34000000, 0x36000000):
            names = {0x34000000: ("cbz", "cbnz"), 0x36000000: ("tbz", "tbnz")}[w & 0x7E000000]
            a, b = names if not (w >> 24) & 1 else names[::-1]
            return data[off:off + 4], struct.pack(e + "I", w ^ 0x01000000), f"{a} -> {b}"
        raise PatchError("not an AArch64 conditional branch (b.cond / cbz / cbnz / tbz / tbnz)")
    if arch in ("mips", "mips64"):
        (w,) = struct.unpack_from(e + "I", data, off)
        op = w >> 26
        pairs = {4: "beq<->bne", 5: "beq<->bne", 0x14: "beql<->bnel", 0x15: "beql<->bnel", 6: "blez<->bgtz", 7: "blez<->bgtz"}
        if op in pairs and (op not in (6, 7) or (w >> 16) & 0x1F == 0):
            return data[off:off + 4], struct.pack(e + "I", w ^ (1 << 26)), pairs[op]
        raise PatchError("not a MIPS beq/bne/blez/bgtz instruction")
    raise PatchError(f"branch inversion not implemented for architecture {arch!r}")


def resolve_offset(pb: Optional[ParsedBinary], value: int, is_vaddr: bool) -> int:
    if not is_vaddr:
        return value
    if pb is None:
        raise PatchError("virtual addresses need a recognised ELF/PE/Mach-O file")
    off = pb.vaddr_to_offset(value)
    if off is None:
        raise PatchError(f"virtual address 0x{value:x} is not backed by file data")
    return off


def fix_pe_checksum(buf: bytearray) -> Optional[int]:
    if buf[:2] != b"MZ":
        return None
    (lfanew,) = struct.unpack_from("<I", buf, 0x3C)
    if bytes(buf[lfanew:lfanew + 4]) != b"PE\0\0":
        return None
    off = lfanew + 24 + 64
    new = pe_checksum(bytes(buf), off)
    struct.pack_into("<I", buf, off, new)
    return new


def apply_patches(src: str | Path, ops: list[PatchOp], out: str | Path | None = None, in_place: bool = False,
                  dry_run: bool = False, force: bool = False, fix_checksum: bool = False) -> dict[str, Any]:
    src = Path(src)
    data = bytearray(src.read_bytes())
    changes = []
    for op in ops:
        end = op.offset + len(op.new)
        if op.offset < 0 or end > len(data):
            raise PatchError(f"patch at 0x{op.offset:x} (+{len(op.new)}) is outside the file ({len(data)} bytes)")
        old = bytes(data[op.offset:end])
        if op.expect is not None and old != op.expect and not force:
            raise PatchError(f"refusing to patch 0x{op.offset:x}: expected {op.expect.hex()} but found {old.hex()} (use --force to override)")
        data[op.offset:end] = op.new
        changes.append({"offset": op.offset, "old": old.hex(), "new": op.new.hex(), "description": op.description,
                        "unchanged": old == op.new})
    result: dict[str, Any] = {"source": str(src), "changes": changes, "dry_run": dry_run}
    if fix_checksum:
        result["pe_checksum"] = fix_pe_checksum(data)
    if dry_run:
        result["output"] = None
        return result
    if in_place:
        backup = src.with_name(src.name + ".bak")
        if not backup.exists():
            shutil.copy2(src, backup)
            result["backup"] = str(backup)
        target = src
    else:
        target = Path(out) if out else src.with_name(src.name + ".patched")
        shutil.copy2(src, target)
    target.write_bytes(bytes(data))
    check = target.read_bytes()
    for ch in changes:
        o = ch["offset"]
        if check[o:o + len(ch["new"]) // 2].hex() != ch["new"]:
            raise PatchError("post-write verification failed")
    result["output"] = str(target)
    return result
