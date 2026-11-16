"""Cross-references and ``main`` discovery for x86 / x86-64 without a disassembler.

Finds the code that references a string or data address (``lea reg,[rip+x]``, ``mov reg,[rip+x]``,
``push imm32``, absolute operands) and direct ``call``/``jmp`` to a function. This is how you
get from "Wrong password" to the validation routine in a stripped crackme in one command.
"""
from __future__ import annotations

import bisect
import re
import struct
from typing import Any, Optional

from .binary import ParsedBinary

_PROLOGUES = (b"\xf3\x0f\x1e\xfa", b"\xf3\x0f\x1e\xfb", b"\x55\x48\x89\xe5", b"\x55\x89\xe5")


def exec_ranges(pb: ParsedBinary, data: bytes) -> list[tuple[int, int]]:
    ranges = [(s.offset, s.offset + s.size) for s in pb.sections if s.executable and s.size]
    if not ranges:
        ranges = [(sg.offset, sg.offset + sg.size) for sg in pb.segments if "x" in sg.flags and sg.size]
    return [(a, min(b, len(data))) for a, b in ranges] or [(0, len(data))]


def guess_function_start(data: bytes, pb: ParsedBinary, off: int, window: int = 0x2000) -> Optional[int]:
    """Best-effort function start (file offset) at or before ``off``."""
    lo = max(0, off - window)
    best = None
    for pro in _PROLOGUES:
        i = data.rfind(pro, lo, off + 1)
        if i != -1 and (best is None or i > best):
            best = i
    return best


def _name_for(pb: ParsedBinary, data: bytes, off: int) -> dict[str, Any]:
    va = pb.offset_to_vaddr(off)
    info: dict[str, Any] = {}
    if va is not None:
        sym = pb.symbol_at(va)
        if sym:
            return {"name": sym.name, "address": sym.value, "method": "symbol"}
    start = guess_function_start(data, pb, off)
    if start is not None:
        sva = pb.offset_to_vaddr(start)
        info = {"name": f"sub_{sva:x}" if sva is not None else f"sub_off_{start:x}", "address": sva, "method": "prologue-guess"}
    return info


_RIPREL = re.compile(rb"(?=([\x40-\x4f]?)([\x8b\x8d\x89])([\x05\x0d\x15\x1d\x25\x2d\x35\x3d])(.{4}))", re.S)
_BRANCH = re.compile(rb"(?=([\xe8\xe9])(.{4}))", re.S)
_IMM32 = re.compile(rb"(?=([\x68\xb8-\xbf])(.{4}))", re.S)
_IMM32_REX = re.compile(rb"(?=\x48\xc7[\xc0-\xc7](.{4}))", re.S)
_ABS32 = re.compile(rb"(?=([\x8b\x8d\x89\xc7\xa1\xa3])([\x05\x0d\x15\x1d\x25\x2d\x35\x3d])?(.{4}))", re.S)


class XrefIndex:
    """Single-pass index of code references to addresses (x86 / x86-64)."""

    def __init__(self, data: bytes, pb: ParsedBinary, max_code: int = 16 * 1024 * 1024):
        if pb.arch not in ("x86", "x86_64"):
            raise ValueError(f"xref scanning is implemented for x86/x86-64 only (this file is {pb.arch})")
        self.data, self.pb = data, pb
        spans = sorted([(sg.vaddr, sg.vaddr + max(sg.vsize, sg.size)) for sg in pb.segments] +
                       [(sc.vaddr, sc.vaddr + sc.vsize) for sc in pb.sections if sc.vsize])
        self._starts = [a for a, _ in spans]
        self._spans = spans
        self.by_target: dict[int, list[dict[str, Any]]] = {}
        scanned = 0
        for lo, hi in exec_ranges(pb, data):
            hi = min(hi, lo + max(0, max_code - scanned))
            if hi <= lo:
                break
            scanned += hi - lo
            self._scan(lo, hi)
        self.truncated = scanned >= max_code

    def _add(self, target: int, off: int, kind: str, length: int):
        va = self.pb.offset_to_vaddr(off)
        self.by_target.setdefault(target, []).append({"offset": off, "vaddr": va, "kind": kind, "length": length})

    def _mapped(self, va: int) -> bool:
        i = bisect.bisect_right(self._starts, va) - 1
        while i >= 0 and i > len(self._spans) - 40:   # a handful of overlapping spans at most
            if self._spans[i][0] <= va < self._spans[i][1]:
                return True
            i -= 1
        return any(a <= va < b for a, b in self._spans[max(0, i - 1):i + 2]) if i >= 0 else False

    def _scan(self, lo: int, hi: int):
        seg = self.data[lo:hi]
        is64 = self.pb.arch == "x86_64"
        if is64:
            for m in _RIPREL.finditer(seg):
                i = m.start()
                rex, opc = m.group(1), m.group(2)
                if not rex and i > 0 and 0x40 <= seg[i - 1] <= 0x4F:
                    continue  # tail of a REX-prefixed instruction examined at i-1
                length = len(rex) + 6
                va = self.pb.offset_to_vaddr(lo + i)
                if va is None:
                    continue
                (disp,) = struct.unpack("<i", m.group(4))
                kind = {0x8D: "lea", 0x8B: "mov load", 0x89: "mov store"}[opc[0]]
                self._add(va + length + disp, lo + i, kind, length)
        for m in _BRANCH.finditer(seg):
            i = m.start()
            va = self.pb.offset_to_vaddr(lo + i)
            if va is None:
                continue
            (rel,) = struct.unpack("<i", m.group(2))
            target = (va + 5 + rel) & (0xFFFFFFFFFFFFFFFF if is64 else 0xFFFFFFFF)
            if self._mapped(target):
                self._add(target, lo + i, "call" if m.group(1) == b"\xe8" else "jmp", 5)
        for m in _IMM32.finditer(seg):
            (val,) = struct.unpack("<I", m.group(2))
            if self._mapped(val):
                self._add(val, lo + m.start(), "push imm32" if m.group(1) == b"\x68" else "mov imm32", 5)
        if is64:
            for m in _IMM32_REX.finditer(seg):
                (val,) = struct.unpack("<I", m.group(1))
                if self._mapped(val):
                    self._add(val, lo + m.start(), "mov r64,imm32", 7)
        else:
            for m in _ABS32.finditer(seg):
                opc, modrm = m.group(1), m.group(2)
                if opc in (b"\xa1", b"\xa3") and modrm is None:
                    pass
                elif modrm is None:
                    continue
                (val,) = struct.unpack("<I", m.group(3))
                if self._mapped(val):
                    self._add(val, lo + m.start(), "abs operand", 6)

    def refs(self, target: int) -> list[dict[str, Any]]:
        out = []
        for r in self.by_target.get(target, []):
            r = dict(r)
            r["function"] = _name_for(self.pb, self.data, r["offset"])
            out.append(r)
        return sorted(out, key=lambda r: r["offset"])


def find_xrefs(data: bytes, pb: ParsedBinary, target: int, max_results: int = 100,
               index: "XrefIndex | None" = None) -> list[dict[str, Any]]:
    """References to virtual address ``target`` from x86/x86-64 code."""
    idx = index or XrefIndex(data, pb)
    return idx.refs(target)[:max_results]


def find_main(data: bytes, pb: ParsedBinary) -> Optional[dict[str, Any]]:
    """Recover ``main`` from the ``_start`` stub of a (possibly stripped) glibc executable."""
    sym = pb.symbol_by_name("main")
    if sym:
        return {"address": sym.value, "method": "symbol"}
    if pb.format != "ELF" or pb.entry is None or pb.arch not in ("x86", "x86_64"):
        return None
    eo = pb.entry_offset
    if eo is None:
        return None
    stub = data[eo:eo + 0x60]
    if pb.arch == "x86_64":
        for i in range(len(stub) - 7):
            if stub[i:i + 3] in (b"\x48\x8d\x3d", b"\x48\x8d\x35") and stub[i:i + 3] == b"\x48\x8d\x3d":
                (disp,) = struct.unpack_from("<i", stub, i + 3)
                return {"address": pb.entry + i + 7 + disp, "method": "lea rdi,[rip+x] in _start"}
            if stub[i:i + 3] == b"\x48\xc7\xc7":
                (imm,) = struct.unpack_from("<I", stub, i + 3)
                return {"address": imm, "method": "mov rdi,imm32 in _start"}
    else:
        call = stub.rfind(b"\xe8")
        if call > 0:
            push = stub.rfind(b"\x68", 0, call)
            if push >= 0 and push + 5 <= len(stub):
                (imm,) = struct.unpack_from("<I", stub, push + 1)
                return {"address": imm, "method": "push imm32 before __libc_start_main"}
    return None
