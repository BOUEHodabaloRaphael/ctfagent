"""Recover strings built on the stack with immediate ``mov`` instructions (x86 / x86-64).

Handles the encodings emitted by compilers at -O0/-O1 and by many malware builders:
``mov byte/dword [rbp+d], imm`` (C6/C7 /0), RSP-based variants, and
``movabs reg, imm64`` followed by ``mov [rbp+d], reg``.
"""
from __future__ import annotations

import re
import struct
from typing import Any


def _printable_runs(mem: dict[int, int], min_len: int):
    if not mem:
        return
    run: list[tuple[int, int]] = []
    last = None
    for disp in sorted(mem):
        b = mem[disp]
        contiguous = last is not None and disp == last + 1
        if 0x20 <= b < 0x7F and (contiguous or not run):
            run.append((disp, b))
        elif 0x20 <= b < 0x7F:
            if len(run) >= min_len:
                yield run
            run = [(disp, b)]
        else:
            if len(run) >= min_len:
                yield run
            run = []
        last = disp
    if len(run) >= min_len:
        yield run


def _step(data: bytes, i: int, regs: dict[int, bytes]):
    """Decode one recognised instruction at ``i``.

    Returns ``(length, store)`` where ``store`` is ``(disp, bytes)`` for a memory write that
    carries constant data, ``None`` for a recognised register load, or ``False`` if the bytes
    are not a recognised instruction.
    """
    n = len(data)
    b0 = data[i]
    # movabs reg, imm64   (48/49 B8+r)
    if b0 in (0x48, 0x49) and i + 10 <= n and 0xB8 <= data[i + 1] <= 0xBF:
        regs[(data[i + 1] - 0xB8) + (8 if b0 == 0x49 else 0)] = data[i + 2:i + 10]
        return 10, None
    # mov r32, imm32   (B8+r)
    if 0xB8 <= b0 <= 0xBF and i + 5 <= n:
        regs[b0 - 0xB8] = data[i + 1:i + 5]
        return 5, None
    # mov byte/dword [base+disp], imm
    if b0 == 0xC6 and i + 4 <= n:
        m = data[i + 1]
        if m == 0x45:
            return 4, (struct.unpack_from("<b", data, i + 2)[0], data[i + 3:i + 4])
        if m == 0x85 and i + 7 <= n:
            return 7, (struct.unpack_from("<i", data, i + 2)[0], data[i + 6:i + 7])
        if m == 0x44 and i + 5 <= n and data[i + 2] == 0x24:
            return 5, (struct.unpack_from("<b", data, i + 3)[0], data[i + 4:i + 5])
    if b0 == 0xC7 and i + 7 <= n:
        m = data[i + 1]
        if m == 0x45:
            return 7, (struct.unpack_from("<b", data, i + 2)[0], data[i + 3:i + 7])
        if m == 0x85 and i + 10 <= n:
            return 10, (struct.unpack_from("<i", data, i + 2)[0], data[i + 6:i + 10])
        if m == 0x44 and i + 8 <= n and data[i + 2] == 0x24:
            return 8, (struct.unpack_from("<b", data, i + 3)[0], data[i + 4:i + 8])
    # mov [base+disp], reg   (89 /r, optional REX.W / REX.WR)
    j = i
    size, rexr = 4, 0
    if b0 in (0x48, 0x4C):
        size, rexr, j = 8, (8 if b0 == 0x4C else 0), i + 1
    if j + 3 <= n and data[j] == 0x89:
        m = data[j + 1]
        reg = ((m >> 3) & 7) + rexr
        if m & 0xC7 == 0x45 and j + 3 <= n:
            store = (struct.unpack_from("<b", data, j + 2)[0], regs.get(reg))
            return (j + 3) - i, (store[0], store[1][:size]) if store[1] else None
        if m & 0xC7 == 0x85 and j + 6 <= n:
            d = struct.unpack_from("<i", data, j + 2)[0]
            return (j + 6) - i, (d, regs[reg][:size]) if reg in regs else None
        if m & 0xC7 == 0x44 and j + 4 <= n and data[j + 2] == 0x24:
            d = struct.unpack_from("<b", data, j + 3)[0]
            return (j + 4) - i, (d, regs[reg][:size]) if reg in regs else None
    return False


_START = re.compile(
    rb"(?=(?:\xc6[\x45\x85\x44]|\xc7[\x45\x85\x44]|[\x48\x49][\xb8-\xbf]"
    rb"|[\xb8-\xbf].{4}[\x48\x4c]?\x89[\x45\x4d\x55\x5d\x65\x6d\x75\x7d\x85\x44]))", re.S)
_LEAD = frozenset([0x48, 0x49, 0x4C, 0x89, 0xC6, 0xC7] + list(range(0xB8, 0xC0)))


def find_stack_strings(data: bytes, start: int = 0, end: int | None = None, min_len: int = 5,
                       max_results: int = 200) -> list[dict[str, Any]]:
    """Scan ``data[start:end]``. Candidate chain starts are located with a C-speed regex."""
    end = len(data) if end is None else min(end, len(data))
    results: list[dict[str, Any]] = []
    window = data[:end]
    next_free = start
    for m in _START.finditer(window, start, end):
        if m.start() < next_free:
            continue
        i = m.start()
        chain: list[tuple[int, bytes]] = []
        regs: dict[int, bytes] = {}
        chain_start = i
        while i < end:
            step = _step(window, i, regs) if window[i] in _LEAD else False
            if step is False:
                break
            length, store = step
            if store:
                chain.append(store)
            i += length
        next_free = max(i, m.start() + 1)
        if len(chain) >= 2:
            mem: dict[int, int] = {}
            for disp, raw in chain:
                for k, byte in enumerate(raw):
                    mem[disp + k] = byte
            for run in _printable_runs(mem, min_len):
                results.append({"offset": chain_start, "encoding": "stack",
                                "value": "".join(chr(b) for _, b in run), "instructions": len(chain)})
        if len(results) >= max_results:
            break
    return results
