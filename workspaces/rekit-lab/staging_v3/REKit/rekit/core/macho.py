"""Compact Mach-O parser (thin 32/64-bit images and fat/universal wrappers)."""
from __future__ import annotations

import struct

from .binary import ParsedBinary, ParseError, Section, Segment, Symbol, cstr, unpack
from .util import entropy

CPU = {7: ("x86", "x86"), 0x01000007: ("x86_64", "x86-64"), 12: ("arm", "ARM"),
       0x0100000C: ("aarch64", "ARM64"), 18: ("ppc", "PowerPC"), 0x01000012: ("ppc64", "PowerPC64")}
FILETYPES = {1: "object", 2: "executable", 3: "fvmlib", 4: "core", 5: "preload", 6: "dylib",
             7: "dylinker", 8: "bundle", 9: "dylib stub", 10: "dsym", 11: "kext"}
LC_SEGMENT, LC_SYMTAB, LC_LOAD_DYLIB, LC_UUID, LC_SEGMENT_64 = 0x1, 0x2, 0xC, 0x1B, 0x19
LC_CODE_SIGNATURE, LC_ENCRYPTION_INFO, LC_ENCRYPTION_INFO_64, LC_MAIN = 0x1D, 0x21, 0x2C, 0x80000028
LC_LOAD_WEAK_DYLIB, LC_REEXPORT_DYLIB, LC_RPATH = 0x80000018, 0x8000001F, 0x8000001C
MH_PIE, MH_NO_HEAP_EXECUTION, MH_ALLOW_STACK_EXECUTION = 0x200000, 0x1000000, 0x20000

FAT_MAGICS = (b"\xca\xfe\xba\xbe", b"\xbe\xba\xfe\xca")
THIN_MAGICS = {b"\xcf\xfa\xed\xfe": ("<", 64), b"\xce\xfa\xed\xfe": ("<", 32),
               b"\xfe\xed\xfa\xcf": (">", 64), b"\xfe\xed\xfa\xce": (">", 32)}


def is_fat(data: bytes) -> bool:
    """cafebabe is shared with Java classes: a fat header has a small architecture count."""
    return data[:4] == b"\xca\xfe\xba\xbe" and len(data) >= 8 and struct.unpack(">I", data[4:8])[0] < 45


def looks_macho(data: bytes) -> bool:
    return data[:4] in THIN_MAGICS or is_fat(data)


def parse_macho(data: bytes) -> ParsedBinary:
    if is_fat(data):
        n = struct.unpack(">I", data[4:8])[0]
        slices = []
        for i in range(min(n, 16)):
            cpu, _sub, off, size, _al = unpack(">IIIII", data, 8 + 20 * i)
            slices.append({"arch": CPU.get(cpu, ("unknown", hex(cpu)))[1], "offset": off, "size": size})
        if not slices:
            raise ParseError("empty fat header")
        pick = next((s for s in slices if "64" in s["arch"]), slices[0])
        inner = parse_macho(data[pick["offset"]:pick["offset"] + pick["size"]])
        inner.metadata["fat_slices"] = slices
        inner.metadata["analysed_slice"] = pick["arch"]
        inner.warnings.append("universal binary: offsets/addresses refer to the analysed slice only")
        return inner

    magic = data[:4]
    if magic not in THIN_MAGICS:
        raise ParseError("not a Mach-O file")
    e, bits = THIN_MAGICS[magic]
    hdr = 32 if bits == 64 else 28
    cputype, _sub, filetype, ncmds, sizeofcmds, flags = unpack(e + "iiIIII", data, 4)[0:6]
    arch, mname = CPU.get(cputype & 0xFFFFFFFF, ("unknown", f"unknown({cputype})"))
    pb = ParsedBinary(format="Mach-O", bits=bits, endian="little" if e == "<" else "big", arch=arch,
                      machine=mname, kind=FILETYPES.get(filetype, str(filetype)), file_size=len(data))
    pb.metadata["flags"] = flags
    off = hdr
    text_base = None
    entryoff = None
    dylibs: list[str] = []
    symtab = None
    for _ in range(min(ncmds, 512)):
        try:
            cmd, size = unpack(e + "II", data, off)
        except ParseError:
            pb.warnings.append("load commands truncated")
            break
        if size < 8 or off + size > len(data):
            pb.warnings.append("malformed load command size")
            break
        if cmd in (LC_SEGMENT, LC_SEGMENT_64):
            if cmd == LC_SEGMENT_64:
                segname, vmaddr, vmsize, fileoff, filesize, _mp, initprot, nsects, _fl = unpack(e + "16sQQQQiiII", data, off + 8)
                sec_fmt, sec_size, sec_start = e + "16s16sQQIIIIIIII", 80, off + 72
            else:
                segname, vmaddr, vmsize, fileoff, filesize, _mp, initprot, nsects, _fl = unpack(e + "16sIIIIiiII", data, off + 8)
                sec_fmt, sec_size, sec_start = e + "16s16sIIIIIIIII", 68, off + 56
            sname = segname.split(b"\0")[0].decode("latin-1")
            prot = ("r" if initprot & 1 else "-") + ("w" if initprot & 2 else "-") + ("x" if initprot & 4 else "-")
            pb.segments.append(Segment(vaddr=vmaddr, vsize=vmsize, offset=fileoff, size=filesize, flags=prot, name=sname))
            if sname == "__TEXT" and fileoff == 0:
                text_base = vmaddr
            for i in range(min(nsects, 256)):
                try:
                    f = unpack(sec_fmt, data, sec_start + i * sec_size)
                except ParseError:
                    break
                nm = f[0].split(b"\0")[0].decode("latin-1")
                s = Section(name=f"{sname},{nm}", offset=f[4], size=f[3] if f[4] else 0, vaddr=f[2],
                            vsize=f[3], flags=prot, index=len(pb.sections))
                if s.size and s.offset + s.size <= len(data):
                    s.entropy = entropy(data[s.offset:s.offset + s.size])
                pb.sections.append(s)
        elif cmd in (LC_LOAD_DYLIB, LC_LOAD_WEAK_DYLIB, LC_REEXPORT_DYLIB):
            (name_off,) = unpack(e + "I", data, off + 8)
            dylibs.append(cstr(data, off + name_off, 512))
        elif cmd == LC_RPATH:
            (name_off,) = unpack(e + "I", data, off + 8)
            pb.metadata.setdefault("rpaths", []).append(cstr(data, off + name_off, 512))
        elif cmd == LC_MAIN:
            entryoff = unpack(e + "Q", data, off + 8)[0]
        elif cmd == LC_UUID:
            pb.metadata["uuid"] = data[off + 8:off + 24].hex()
        elif cmd == LC_CODE_SIGNATURE:
            pb.metadata["code_signature"] = True
        elif cmd in (LC_ENCRYPTION_INFO, LC_ENCRYPTION_INFO_64):
            pb.metadata["encrypted"] = unpack(e + "III", data, off + 8)[2] != 0
        elif cmd == LC_SYMTAB:
            symtab = unpack(e + "IIII", data, off + 8)
        off += size
    pb.metadata["dylibs"] = dylibs
    if text_base is not None and entryoff is not None:
        pb.entry = text_base + entryoff
    if symtab:
        symoff, nsyms, stroff, strsize = symtab
        entsz = 16 if bits == 64 else 12
        for i in range(min(nsyms, 100_000)):
            try:
                if bits == 64:
                    n_strx, n_type, n_sect, _desc, n_value = unpack(e + "IBBHQ", data, symoff + i * entsz)
                else:
                    n_strx, n_type, n_sect, _desc, n_value = unpack(e + "IBBhI", data, symoff + i * entsz)
            except ParseError:
                break
            name = cstr(data, stroff + n_strx, 512) if n_strx < strsize else ""
            undefined = (n_type & 0x0E) == 0 and bool(n_type & 0x01) and n_sect == 0
            pb.symbols.append(Symbol(name=name, value=n_value, kind="FUNC" if n_sect else "NOTYPE",
                                     bind="GLOBAL" if n_type & 1 else "LOCAL", shndx=n_sect, imported=undefined and bool(name)))
        seen = set()
        for s in pb.symbols:
            if s.imported and s.name not in seen:
                seen.add(s.name)
                pb.imports.append({"lib": "", "name": s.name})
    pb.protections = {"pie": "yes" if flags & MH_PIE else "no",
                      "stack_executable": bool(flags & MH_ALLOW_STACK_EXECUTION),
                      "code_signed": bool(pb.metadata.get("code_signature")),
                      "encrypted": bool(pb.metadata.get("encrypted"))}
    pb.protections["nx_heap"] = bool(flags & MH_NO_HEAP_EXECUTION)
    pb.protections["stripped"] = not any(not s.imported and s.name for s in pb.symbols)
    return pb
