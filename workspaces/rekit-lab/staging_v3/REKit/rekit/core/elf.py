"""Pure-Python ELF parser (32/64-bit, little/big endian).

No dependency on ``readelf``. Symbol names are read straight from the string tables,
so versioned names (``foo@GLIBC_2.4``) and stripped binaries are handled correctly.
"""
from __future__ import annotations

import re
import shutil
from pathlib import Path
from typing import Any

from .binary import ParsedBinary, ParseError, Section, Segment, Symbol, cstr, unpack
from .util import entropy

MACHINES = {
    0: "none", 2: "SPARC", 3: "x86", 4: "m68k", 8: "MIPS", 20: "PowerPC", 21: "PowerPC64",
    22: "S390", 40: "ARM", 42: "SuperH", 43: "SPARC V9", 50: "IA-64", 62: "x86-64",
    94: "Xtensa", 183: "AArch64", 243: "RISC-V", 247: "eBPF", 258: "LoongArch",
}
ARCH_NORMALISED = {
    3: "x86", 62: "x86_64", 40: "arm", 183: "aarch64", 8: "mips", 20: "ppc", 21: "ppc64",
    243: "riscv", 42: "sh", 43: "sparc", 2: "sparc", 22: "s390", 247: "ebpf",
}
ET_NAMES = {0: "none", 1: "relocatable", 2: "executable", 3: "shared object / PIE", 4: "core"}
SH_TYPES = {0: "NULL", 1: "PROGBITS", 2: "SYMTAB", 3: "STRTAB", 4: "RELA", 5: "HASH",
            6: "DYNAMIC", 7: "NOTE", 8: "NOBITS", 9: "REL", 11: "DYNSYM", 14: "INIT_ARRAY",
            15: "FINI_ARRAY", 0x6ffffff6: "GNU_HASH", 0x6ffffffe: "VERNEED", 0x6fffffff: "VERSYM"}
SYM_TYPES = {0: "NOTYPE", 1: "OBJECT", 2: "FUNC", 3: "SECTION", 4: "FILE", 5: "COMMON",
             6: "TLS", 10: "GNU_IFUNC"}
SYM_BINDS = {0: "LOCAL", 1: "GLOBAL", 2: "WEAK", 10: "GNU_UNIQUE"}

PT_LOAD, PT_DYNAMIC, PT_INTERP, PT_GNU_STACK, PT_GNU_RELRO = 1, 2, 3, 0x6474E551, 0x6474E552
DT_NEEDED, DT_PLTRELSZ, DT_HASH, DT_STRTAB, DT_SYMTAB, DT_STRSZ, DT_SYMENT = 1, 2, 4, 5, 6, 10, 11
DT_SONAME, DT_RPATH, DT_TEXTREL, DT_BIND_NOW, DT_RUNPATH, DT_FLAGS = 14, 15, 22, 24, 29, 30
DT_FLAGS_1 = 0x6FFFFFFB
DF_TEXTREL, DF_BIND_NOW, DF_1_NOW, DF_1_PIE = 0x4, 0x8, 0x1, 0x08000000

STANDARD_SECTIONS = {
    "", ".text", ".data", ".bss", ".rodata", ".comment", ".symtab", ".strtab", ".shstrtab",
    ".dynamic", ".dynsym", ".dynstr", ".hash", ".gnu.hash", ".gnu.version", ".gnu.version_r",
    ".gnu.version_d", ".rela.dyn", ".rela.plt", ".rel.dyn", ".rel.plt", ".plt", ".plt.got",
    ".plt.sec", ".init", ".fini", ".init_array", ".fini_array", ".eh_frame", ".eh_frame_hdr",
    ".got", ".got.plt", ".interp", ".note.gnu.build-id", ".note.ABI-tag", ".note.gnu.property",
    ".tdata", ".tbss", ".data.rel.ro", ".gcc_except_table", ".ctors", ".dtors", ".jcr",
    ".note.gnu.gold-version", ".gnu_debuglink", ".stab", ".stabstr", ".preinit_array",
    ".data1", ".rodata1", ".text.unlikely", ".text.startup", ".text.hot",
}
FORTIFY_RE = re.compile(r"^__(?!stack_chk)\w+_chk$")


def _flags_from_sh(flags: int) -> str:
    return ("r" if flags & 2 else "-") + ("w" if flags & 1 else "-") + ("x" if flags & 4 else "-")


def _flags_from_ph(flags: int) -> str:
    return ("r" if flags & 4 else "-") + ("w" if flags & 2 else "-") + ("x" if flags & 1 else "-")


def _read_symbols(data: bytes, e: str, bits: int, sym_off: int, count: int, str_off: int,
                  str_size: int, limit: int = 200_000) -> list[Symbol]:
    out: list[Symbol] = []
    entsize = 24 if bits == 64 else 16
    count = min(count, limit, max(0, (len(data) - sym_off) // entsize))
    for i in range(count):
        base = sym_off + i * entsize
        if bits == 64:
            name, info, _other, shndx, value, size = unpack(e + "IBBHQQ", data, base)
        else:
            name, value, size, info, _other, shndx = unpack(e + "IIIBBH", data, base)
        if i == 0:
            continue
        nm = cstr(data, str_off + name, 512) if name < max(str_size, 1) else ""
        out.append(Symbol(name=nm, value=value, size=size,
                          kind=SYM_TYPES.get(info & 0xF, str(info & 0xF)),
                          bind=SYM_BINDS.get(info >> 4, str(info >> 4)),
                          shndx=shndx, imported=(shndx == 0 and bool(nm))))
    return out


def parse_elf(data: bytes) -> ParsedBinary:
    if len(data) < 52 or data[:4] != b"\x7fELF":
        raise ParseError("not an ELF file")
    ei_class, ei_data = data[4], data[5]
    if ei_class not in (1, 2) or ei_data not in (1, 2):
        raise ParseError("invalid ELF class/data encoding")
    bits = 32 if ei_class == 1 else 64
    e = "<" if ei_data == 1 else ">"
    if bits == 64:
        (e_type, e_machine, _ver, e_entry, e_phoff, e_shoff, e_flags, _ehsize, e_phentsize,
         e_phnum, e_shentsize, e_shnum, e_shstrndx) = unpack(e + "HHIQQQIHHHHHH", data, 16)
    else:
        (e_type, e_machine, _ver, e_entry, e_phoff, e_shoff, e_flags, _ehsize, e_phentsize,
         e_phnum, e_shentsize, e_shnum, e_shstrndx) = unpack(e + "HHIIIIIHHHHHH", data, 16)

    pb = ParsedBinary(format="ELF", bits=bits, endian="little" if ei_data == 1 else "big",
                      arch=ARCH_NORMALISED.get(e_machine, "unknown"),
                      machine=MACHINES.get(e_machine, f"unknown({e_machine})"),
                      kind=ET_NAMES.get(e_type, f"unknown({e_type})"), entry=e_entry or None,
                      file_size=len(data))
    if e_machine == 8 and bits == 64:
        pb.arch = "mips64"
    if e_machine == 40 and e_entry & 1:
        pb.metadata["thumb_entry"] = True
    pb.metadata.update(osabi=data[7], e_flags=e_flags, e_type=e_type, e_machine=e_machine)

    # ---- program headers ---------------------------------------------------
    phdrs: list[dict[str, int]] = []
    if e_phoff and e_phnum:
        want = 56 if bits == 64 else 32
        if e_phentsize < want:
            pb.warnings.append(f"unexpected e_phentsize={e_phentsize}")
        else:
            for i in range(min(e_phnum, 512)):
                off = e_phoff + i * e_phentsize
                try:
                    if bits == 64:
                        t, fl, po, va, _pa, fsz, msz, al = unpack(e + "IIQQQQQQ", data, off)
                    else:
                        t, po, va, _pa, fsz, msz, fl, al = unpack(e + "IIIIIIII", data, off)
                except ParseError:
                    pb.warnings.append("program header table truncated")
                    break
                phdrs.append(dict(type=t, flags=fl, offset=po, vaddr=va, filesz=fsz, memsz=msz))
                if t == PT_LOAD:
                    pb.segments.append(Segment(vaddr=va, vsize=msz, offset=po, size=fsz,
                                               flags=_flags_from_ph(fl), name=f"LOAD#{i}"))
    # ---- section headers ---------------------------------------------------
    raw_secs: list[dict[str, Any]] = []
    if e_shoff and e_shentsize >= (64 if bits == 64 else 40):
        try:
            def sh_at(i: int):
                off = e_shoff + i * e_shentsize
                if bits == 64:
                    return unpack(e + "IIQQQQIIQQ", data, off)
                return unpack(e + "IIIIIIIIII", data, off)
            if e_shnum == 0:  # extended numbering
                e_shnum = sh_at(0)[5] if e_shoff < len(data) else 0
            if e_shstrndx == 0xFFFF:
                e_shstrndx = sh_at(0)[6]
            if e_shnum > 4096 or e_shoff + e_shnum * e_shentsize > len(data):
                pb.warnings.append(f"section header table out of range (shnum={e_shnum}); clamped")
                e_shnum = max(0, min(e_shnum, 4096, (len(data) - e_shoff) // e_shentsize))
            for i in range(e_shnum):
                nm, t, fl, addr, off, size, link, info, _al, entsz = sh_at(i)
                raw_secs.append(dict(index=i, name_off=nm, type=t, flags=fl, addr=addr,
                                     offset=off, size=size, link=link, info=info, entsize=entsz))
        except ParseError:
            pb.warnings.append("section header table truncated")
    pb.metadata["section_headers_present"] = bool(raw_secs)

    shstr_off = 0
    if raw_secs and e_shstrndx < len(raw_secs):
        shstr_off = raw_secs[e_shstrndx]["offset"]
    for r in raw_secs:
        r["name"] = cstr(data, shstr_off + r["name_off"], 128) if shstr_off else ""
        nobits = r["type"] == 8
        sec = Section(name=r["name"], offset=r["offset"], size=0 if nobits else r["size"],
                      vaddr=r["addr"], vsize=r["size"] if r["flags"] & 2 else 0,
                      flags=_flags_from_sh(r["flags"]), kind=SH_TYPES.get(r["type"], hex(r["type"])),
                      index=r["index"])
        if sec.size and sec.offset + sec.size <= len(data) and r["type"] != 0:
            sec.entropy = entropy(data[sec.offset:sec.offset + sec.size])
        elif sec.size and sec.offset + sec.size > len(data):
            pb.warnings.append(f"section {r['name']!r} extends past end of file")
        if r["type"] != 0:
            pb.sections.append(sec)

    # ---- dynamic segment / section ------------------------------------------
    dyn: dict[int, list[int]] = {}
    dyn_off = None
    for p in phdrs:
        if p["type"] == PT_DYNAMIC:
            dyn_off, dyn_size = p["offset"], p["filesz"]
    if dyn_off is None:
        for r in raw_secs:
            if r["type"] == 6:
                dyn_off, dyn_size = r["offset"], r["size"]
    if dyn_off is not None:
        step = 16 if bits == 64 else 8
        for i in range(min(dyn_size // step, 4096)):
            try:
                tag, val = unpack(e + ("qQ" if bits == 64 else "iI"), data, dyn_off + i * step)
            except ParseError:
                break
            if tag == 0:
                break
            dyn.setdefault(tag, []).append(val)

    def v2o(va: int):
        return pb.vaddr_to_offset(va)

    needed: list[str] = []
    dynstr_off = None
    if DT_STRTAB in dyn:
        dynstr_off = v2o(dyn[DT_STRTAB][0])
    if dynstr_off is not None:
        needed = [cstr(data, dynstr_off + v, 256) for v in dyn.get(DT_NEEDED, [])]
        for key, tag in (("soname", DT_SONAME), ("rpath", DT_RPATH), ("runpath", DT_RUNPATH)):
            if tag in dyn:
                pb.metadata[key] = cstr(data, dynstr_off + dyn[tag][0], 512)
    pb.metadata["needed"] = needed
    interp = None
    for p in phdrs:
        if p["type"] == PT_INTERP:
            interp = cstr(data, p["offset"], min(p["filesz"], 256) or 256)
    pb.metadata["interpreter"] = interp

    # ---- symbols ---------------------------------------------------------------
    have_symtab = False
    for r in raw_secs:
        if r["type"] in (2, 11) and r["link"] < len(raw_secs):
            strsec = raw_secs[r["link"]]
            try:
                syms = _read_symbols(data, e, bits, r["offset"], r["size"] // (24 if bits == 64 else 16),
                                     strsec["offset"], strsec["size"])
            except ParseError:
                pb.warnings.append(f"symbol table {r['name']} truncated")
                continue
            if r["type"] == 2:
                have_symtab = True
            pb.symbols.extend(syms)
    if not pb.symbols and DT_SYMTAB in dyn and dynstr_off is not None:
        # sections stripped: recover dynsym from the dynamic segment
        sym_off = v2o(dyn[DT_SYMTAB][0])
        if sym_off is not None:
            ent = 24 if bits == 64 else 16
            count = 0
            if DT_HASH in dyn and v2o(dyn[DT_HASH][0]) is not None:
                try:
                    count = unpack(e + "II", data, v2o(dyn[DT_HASH][0]))[1]
                except ParseError:
                    count = 0
            if not count and dynstr_off > sym_off:
                count = (dynstr_off - sym_off) // ent
            strsz = dyn.get(DT_STRSZ, [0])[0]
            try:
                pb.symbols = _read_symbols(data, e, bits, sym_off, count, dynstr_off, strsz)
                pb.metadata["symbols_from"] = "dynamic segment (section headers absent)"
            except ParseError:
                pb.warnings.append("could not recover dynamic symbols")

    seen: set[str] = set()
    seen_exp: set[str] = set()
    for s in pb.symbols:
        if s.imported and s.name not in seen and s.kind != "SECTION":
            seen.add(s.name)
            pb.imports.append({"lib": "", "name": s.name, "kind": s.kind})
        elif (e_type == 3 and not s.imported and s.bind in ("GLOBAL", "WEAK") and s.value and s.shndx != 0
              and s.kind in ("FUNC", "OBJECT") and s.name not in seen_exp and len(pb.exports) < 5000):
            seen_exp.add(s.name)
            pb.exports.append({"name": s.name, "address": s.value})

    # ---- notes / comment -------------------------------------------------------
    for r in raw_secs:
        if r["type"] == 7 and r["size"] >= 12:
            try:
                namesz, descsz, ntype = unpack(e + "III", data, r["offset"])
                name = data[r["offset"] + 12:r["offset"] + 12 + namesz].rstrip(b"\0")
                d0 = r["offset"] + 12 + ((namesz + 3) & ~3)
                if name == b"GNU" and ntype == 3:
                    pb.metadata["build_id"] = data[d0:d0 + descsz].hex()
            except ParseError:
                pass
        if r["name"] == ".comment" and r["size"] < 4096:
            parts = [x.decode("latin-1") for x in data[r["offset"]:r["offset"] + r["size"]].split(b"\0") if x]
            pb.metadata["compiler_comments"] = sorted(set(parts))

    # ---- protections -----------------------------------------------------------
    prot = pb.protections
    gnu_stack = next((p for p in phdrs if p["type"] == PT_GNU_STACK), None)
    if gnu_stack is not None:
        fl = gnu_stack["flags"]
        prot["gnu_stack_flags"] = ("R" if fl & 4 else "") + ("W" if fl & 2 else "") + ("E" if fl & 1 else "")
        prot["nx"] = "no" if fl & 1 else "yes"
    else:
        prot["nx"] = "no"
        prot["gnu_stack_flags"] = "absent"
        prot["nx_note"] = "no PT_GNU_STACK header: the kernel assumes an executable stack on most architectures"
    flags1 = dyn.get(DT_FLAGS_1, [0])[0]
    flags = dyn.get(DT_FLAGS, [0])[0]
    if e_type == 2:
        prot["pie"] = "no"
    elif e_type == 3:
        if flags1 & DF_1_PIE:
            prot["pie"] = "yes"
        elif interp:
            prot["pie"] = "likely"
        else:
            prot["pie"] = "no"
            prot["pie_note"] = "ET_DYN without interpreter: shared object, not a PIE executable"
    else:
        prot["pie"] = "no"
    has_relro = any(p["type"] == PT_GNU_RELRO for p in phdrs)
    now = (DT_BIND_NOW in dyn) or bool(flags & DF_BIND_NOW) or bool(flags1 & DF_1_NOW)
    prot["relro"] = ("full" if now else "partial") if has_relro else "no"
    names = {s.name for s in pb.symbols}
    if names:
        prot["canary"] = "yes" if names & {"__stack_chk_fail", "__stack_chk_guard", "__intel_security_cookie"} else "not detected"
        prot["fortify"] = "yes" if any(FORTIFY_RE.match(n) for n in names) else "not detected"
    else:
        prot["canary"] = prot["fortify"] = "unknown"
        prot["symbols_note"] = "no symbols available (stripped static binary?): canary/fortify cannot be determined statically"
    prot["rwx_segments"] = sum(1 for s in pb.segments if "w" in s.flags and "x" in s.flags)
    prot["textrel"] = (DT_TEXTREL in dyn) or bool(flags & DF_TEXTREL)
    prot["stripped"] = not have_symtab
    prot["static"] = interp is None and not needed and e_type != 3
    prot["no_section_headers"] = not raw_secs

    # ---- overlay -----------------------------------------------------------------
    end = 0
    for s in pb.sections:
        end = max(end, s.offset + s.size)
    for sg in pb.segments:
        end = max(end, sg.offset + sg.size)
    if e_shoff and raw_secs:
        end = max(end, e_shoff + len(raw_secs) * e_shentsize)
    if e_phoff:
        end = max(end, e_phoff + len(phdrs) * e_phentsize)
    if end and len(data) - end > 0:
        pb.overlay = {"offset": end, "size": len(data) - end}
    return pb


def elf_anomalies(pb: ParsedBinary) -> list[tuple[str, str, str]]:
    """Return (id, title, detail) tuples for structural oddities."""
    out: list[tuple[str, str, str]] = []
    if pb.protections.get("no_section_headers"):
        out.append(("ELF-NOSECT", "No section headers",
                    "The ELF has no section header table (typical of UPX-packed or deliberately stripped files)."))
    if pb.protections.get("rwx_segments"):
        out.append(("ELF-RWX", "Writable and executable segment",
                    f"{pb.protections['rwx_segments']} PT_LOAD segment(s) are both writable and executable."))
    if pb.entry is not None and pb.sections:
        sec = pb.section_for_vaddr(pb.entry)
        if sec is None:
            out.append(("ELF-EP-OUTSIDE", "Entry point outside any section",
                        f"Entry point 0x{pb.entry:x} is not inside a mapped section."))
        elif sec.name not in (".text", ".init", ".plt", ".plt.sec"):
            out.append(("ELF-EP-ODD", "Entry point in unusual section",
                        f"Entry point 0x{pb.entry:x} lies in section {sec.name!r}."))
    odd = [s.name for s in pb.sections if s.name not in STANDARD_SECTIONS
           and not s.name.startswith((".note", ".debug", ".gnu", ".rela", ".rel", ".text.", ".data.", ".rodata.", ".bss.", ".init_array", ".ARM", ".mdebug", ".MIPS", ".reginfo", ".riscv", ".sdata", ".sbss", ".got"))]
    if odd:
        out.append(("ELF-ODD-SECT", "Non-standard section names", ", ".join(odd[:20])))
    if pb.overlay and pb.overlay["size"] > 0:
        out.append(("ELF-OVERLAY", "Data appended after the ELF structures",
                    f"{pb.overlay['size']} bytes at offset 0x{pb.overlay['offset']:x}."))
    return out


def analyze_elf(path: str | Path, data: bytes) -> dict[str, Any]:
    """Backward-compatible wrapper used by the v3.0 engine API."""
    if not data.startswith(b"\x7fELF"):
        return {"is_elf": False, "available": False}
    try:
        pb = parse_elf(data)
    except ParseError as exc:
        return {"is_elf": True, "available": False, "note": str(exc)}
    return {"is_elf": True, "available": True, "class": f"ELF{pb.bits}", "data": pb.endian,
            "type": pb.kind, "machine": pb.machine, "entry_point": hex(pb.entry or 0),
            "protections": pb.protections, "tool_results": {"parser": "builtin"},
            "readelf_installed": bool(shutil.which("readelf"))}
