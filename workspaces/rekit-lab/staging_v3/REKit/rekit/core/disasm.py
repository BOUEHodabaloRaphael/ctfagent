"""Disassembly front-end: Capstone when installed, ``objdump`` as a fallback."""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .binary import ParsedBinary

try:  # optional dependency
    import capstone as cs
    HAS_CAPSTONE = True
except ImportError:  # pragma: no cover - depends on environment
    cs = None
    HAS_CAPSTONE = False

OBJDUMP_ARCH = {"x86": "i386", "x86_64": "i386:x86-64", "arm": "arm", "aarch64": "aarch64", "mips": "mips",
                "mips64": "mips:isa64", "ppc": "powerpc:common", "ppc64": "powerpc:common64", "riscv": "riscv:rv64"}


def _capstone_params(arch: str, endian: str, mode: str | None):
    big = cs.CS_MODE_BIG_ENDIAN if endian == "big" else cs.CS_MODE_LITTLE_ENDIAN
    table = {
        "x86": (cs.CS_ARCH_X86, cs.CS_MODE_32), "x86_64": (cs.CS_ARCH_X86, cs.CS_MODE_64),
        "arm": (cs.CS_ARCH_ARM, (cs.CS_MODE_THUMB if mode == "thumb" else cs.CS_MODE_ARM) | big),
        "aarch64": (cs.CS_ARCH_ARM64, cs.CS_MODE_ARM | big),
        "mips": (cs.CS_ARCH_MIPS, cs.CS_MODE_MIPS32 | big), "mips64": (cs.CS_ARCH_MIPS, cs.CS_MODE_MIPS64 | big),
        "ppc": (cs.CS_ARCH_PPC, cs.CS_MODE_32 | cs.CS_MODE_BIG_ENDIAN), "ppc64": (cs.CS_ARCH_PPC, cs.CS_MODE_64 | big),
    }
    if arch not in table:
        raise ValueError(f"no Capstone mapping for architecture {arch!r}")
    return table[arch]


def disassemble(data: bytes, pb: ParsedBinary | None, file_offset: int, vaddr: int | None, count: int = 40,
                arch: str | None = None, mode: str | None = None, length: int = 4096) -> dict[str, Any]:
    arch = arch or (pb.arch if pb else "x86_64")
    endian = pb.endian if pb else "little"
    if mode is None and pb and pb.metadata.get("thumb_entry") and pb.entry is not None and vaddr == pb.entry:
        mode = "thumb"
    base = vaddr if vaddr is not None else file_offset
    chunk = data[file_offset:file_offset + length]
    if not chunk:
        raise ValueError("nothing to disassemble at that offset")
    if HAS_CAPSTONE:
        carch, cmode = _capstone_params(arch, endian, mode)
        md = cs.Cs(carch, cmode)
        out = []
        for ins in md.disasm(chunk, base):
            out.append({"address": ins.address, "bytes": ins.bytes.hex(), "mnemonic": ins.mnemonic, "operands": ins.op_str})
            if len(out) >= count:
                break
        return {"engine": "capstone", "arch": arch, "instructions": out}
    exe = shutil.which("objdump")
    if not exe:
        raise RuntimeError("no disassembler available: install capstone (pip install capstone) or binutils (objdump)")
    if arch not in OBJDUMP_ARCH:
        raise RuntimeError(f"objdump fallback does not know architecture {arch!r}; install capstone")
    with tempfile.TemporaryDirectory() as tmp:
        raw = Path(tmp) / "chunk.bin"
        raw.write_bytes(chunk)
        cmd = [exe, "-D", "-b", "binary", "-m", OBJDUMP_ARCH[arch], f"--adjust-vma=0x{base:x}"]
        if arch in ("x86", "x86_64"):
            cmd += ["-M", "intel"]
        if arch == "arm" and mode == "thumb":
            cmd += ["-M", "force-thumb"]
        if endian == "big" and arch in ("arm", "aarch64"):
            cmd[1:1] = ["-EB"]
        proc = subprocess.run(cmd + [str(raw)], capture_output=True, text=True, timeout=30, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"objdump failed: {proc.stderr.strip()[:200]}")
    out = []
    line_re = re.compile(r"^\s*([0-9a-f]+):\t((?:[0-9a-f]{2} )+)\s*\t?(.*)$")
    for line in proc.stdout.splitlines():
        m = line_re.match(line)
        if not m:
            continue
        text = m.group(3).strip()
        if not text and out:   # objdump wraps long encodings onto a continuation line
            out[-1]["bytes"] += m.group(2).replace(" ", "")
            continue
        mnem, _, ops = text.partition(" ")
        out.append({"address": int(m.group(1), 16), "bytes": m.group(2).replace(" ", ""), "mnemonic": mnem, "operands": ops.strip()})
        if len(out) >= count:
            break
    return {"engine": "objdump", "arch": arch, "instructions": out}
