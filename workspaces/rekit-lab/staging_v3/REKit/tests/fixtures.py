"""Hand-built binaries used by the test-suite (no external toolchain required)."""
from __future__ import annotations

import struct


def build_pe(imports: dict[str, list[str]] | None = None, code: bytes = b"\x90" * 16 + b"\xc3",
             section_names=(".text", ".rdata"), plus: bool = True, rwx_text: bool = False,
             extra_data: bytes = b"", overlay: bytes = b"", timestamp: int = 0x5F000000) -> bytes:
    imports = imports or {"kernel32.dll": ["ExitProcess"]}
    fa, sa = 0x200, 0x1000
    text_rva, idata_rva = 0x1000, 0x2000
    ptr = 8 if plus else 4
    # --- import section content ---
    idata = bytearray()
    desc_size = 20 * (len(imports) + 1)
    blobs = []
    pos = desc_size
    layout = []
    for dll, funcs in imports.items():
        thunk_off = pos
        pos += ptr * (len(funcs) + 1)
        names_off = []
        for f in funcs:
            names_off.append(pos)
            pos += 2 + len(f) + 1 + ((len(f) + 1) % 2)
        dll_off = pos
        pos += len(dll) + 1
        layout.append((dll, funcs, thunk_off, names_off, dll_off))
    idata = bytearray(pos + len(extra_data))
    for i, (dll, funcs, thunk_off, names_off, dll_off) in enumerate(layout):
        struct.pack_into("<IIIII", idata, 20 * i, idata_rva + thunk_off, 0, 0, idata_rva + dll_off, idata_rva + thunk_off)
        for k, f in enumerate(funcs):
            struct.pack_into("<Q" if plus else "<I", idata, thunk_off + ptr * k, idata_rva + names_off[k])
            struct.pack_into("<H", idata, names_off[k], k)
            idata[names_off[k] + 2:names_off[k] + 2 + len(f)] = f.encode()
        idata[dll_off:dll_off + len(dll)] = dll.encode()
    idata[pos:pos + len(extra_data)] = extra_data

    def pad(b: bytes, a: int) -> bytes:
        return b + b"\x00" * (-len(b) % a)

    text_raw, idata_raw = pad(code, fa), pad(bytes(idata), fa)
    opt_size = 240 if plus else 224
    headers_size = 0x200
    coff = struct.pack("<HHIIIHH", 0x8664 if plus else 0x14C, 2, timestamp, 0, 0, opt_size, 0x22)
    opt = bytearray(opt_size)
    struct.pack_into("<H", opt, 0, 0x20B if plus else 0x10B)
    struct.pack_into("<I", opt, 16, text_rva)
    if plus:
        struct.pack_into("<Q", opt, 24, 0x140000000)
    else:
        struct.pack_into("<I", opt, 28, 0x400000)
    struct.pack_into("<II", opt, 32, sa, fa)
    struct.pack_into("<III", opt, 56, 0x3000, headers_size, 0)
    struct.pack_into("<HH", opt, 68, 3, 0x8160)
    nrva_off, dd_off = (108, 112) if plus else (92, 96)
    struct.pack_into("<I", opt, nrva_off, 16)
    struct.pack_into("<II", opt, dd_off + 8, idata_rva, desc_size)  # import dir
    tch = 0xE0000020 if rwx_text else 0x60000020
    sec = struct.pack("<8sIIIIIIHHI", section_names[0].encode(), len(code), text_rva, len(text_raw), 0x200, 0, 0, 0, 0, tch)
    sec += struct.pack("<8sIIIIIIHHI", section_names[1].encode(), len(idata), idata_rva, len(idata_raw), 0x200 + len(text_raw), 0, 0, 0, 0, 0x40000040)
    dos = bytearray(0x80)
    dos[:2] = b"MZ"
    struct.pack_into("<I", dos, 0x3C, 0x80)
    hdr = bytes(dos) + b"PE\0\0" + coff + bytes(opt) + sec
    return pad(hdr, headers_size) + text_raw + idata_raw + overlay


def build_elf64(sections=None, code=b"\x90\x90\xc3", imports=("puts",), entry_off=0x1000,
                rwx=False, gnu_stack_flags=6, endian="<") -> bytes:
    """Tiny ELF64 with .text, .dynsym/.dynstr (imports) and .shstrtab."""
    e = endian
    dynstr = b"\0" + b"".join(i.encode() + b"\0" for i in imports)
    dynsym = b"\0" * 24
    off = 1
    for i in imports:
        dynsym += struct.pack(e + "IBBHQQ", off, 0x12, 0, 0, 0, 0)
        off += len(i) + 1
    names = [b"", b".text", b".dynsym", b".dynstr", b".shstrtab"]
    shstr = b"\0"
    name_off = []
    for n in names[1:]:
        name_off.append(len(shstr))
        shstr += n + b"\0"
    base = 0x1000
    text_off = base
    dynsym_off = text_off + len(code)
    dynstr_off = dynsym_off + len(dynsym)
    shstr_off = dynstr_off + len(dynstr)
    shoff = (shstr_off + len(shstr) + 7) & ~7
    body = bytearray(shoff - 0x1000)
    body[0:len(code)] = code
    body[len(code):len(code) + len(dynsym)] = dynsym
    body[dynstr_off - 0x1000:dynstr_off - 0x1000 + len(dynstr)] = dynstr
    body[shstr_off - 0x1000:shstr_off - 0x1000 + len(shstr)] = shstr
    ph_flags = 7 if rwx else 5
    phdrs = struct.pack(e + "IIQQQQQQ", 1, ph_flags, 0, 0x400000, 0x400000, shoff, shoff, 0x1000)
    phdrs += struct.pack(e + "IIQQQQQQ", 0x6474E551, gnu_stack_flags, 0, 0, 0, 0, 0, 16)
    shdrs = struct.pack(e + "IIQQQQIIQQ", 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
    shdrs += struct.pack(e + "IIQQQQIIQQ", name_off[0], 1, 6, 0x400000 + text_off, text_off, len(code), 0, 0, 16, 0)
    shdrs += struct.pack(e + "IIQQQQIIQQ", name_off[1], 11, 2, 0x400000 + dynsym_off, dynsym_off, len(dynsym), 3, 1, 8, 24)
    shdrs += struct.pack(e + "IIQQQQIIQQ", name_off[2], 3, 2, 0x400000 + dynstr_off, dynstr_off, len(dynstr), 0, 0, 1, 0)
    shdrs += struct.pack(e + "IIQQQQIIQQ", name_off[3], 3, 0, 0, shstr_off, len(shstr), 0, 0, 1, 0)
    ehdr = b"\x7fELF" + bytes([2, 1 if e == "<" else 2, 1, 0]) + b"\0" * 8
    ehdr += struct.pack(e + "HHIQQQIHHHHHH", 2, 62, 1, 0x400000 + entry_off, 64, shoff, 0, 64, 56, 2, 64, 5, 4)
    out = bytearray(0x1000)
    out[0:len(ehdr)] = ehdr
    out[64:64 + len(phdrs)] = phdrs
    return bytes(out) + bytes(body) + shdrs


def build_macho64(dylibs=("/usr/lib/libSystem.B.dylib",), pie=True) -> bytes:
    cmds = b""
    seg = struct.pack("<II16sQQQQiiII", 0x19, 72 + 80, b"__TEXT", 0x100000000, 0x1000, 0, 0x1000, 7, 5, 1, 0)
    seg += struct.pack("<16s16sQQIIIIIIII", b"__text", b"__TEXT", 0x100000f00, 0x10, 0xF00, 4, 0, 0, 0x80000400, 0, 0, 0)
    cmds += seg
    for d in dylibs:
        body = struct.pack("<IIII", 24, 0, 0, 0) + d.encode() + b"\0"
        body += b"\0" * (-(8 + len(body)) % 8)
        cmds += struct.pack("<II", 0xC, 8 + len(body)) + body
    cmds += struct.pack("<IIQQ", 0x80000028, 24, 0xF00, 0)
    flags = 0x200000 if pie else 0
    hdr = struct.pack("<IiiIIIII", 0xFEEDFACF, 0x0100000C, 0, 2, 2 + len(dylibs) , len(cmds), flags, 0)
    out = hdr + cmds
    return out + b"\0" * (0x1000 - len(out)) if len(out) < 0x1000 else out


# ---------------------------------------------------------------------------------------
# helpers that need a C toolchain (tests skip cleanly when gcc is absent)
# ---------------------------------------------------------------------------------------
import shutil
import subprocess
import unittest


def need(tool: str):
    if shutil.which(tool) is None:
        raise unittest.SkipTest(f"{tool} not installed")


CRACKME_C = r'''
#include <stdio.h>
#include <string.h>
int check(const char *s){ return strcmp(s, "hunter2") == 0; }
int main(int argc, char **argv){
    if (argc > 1 && check(argv[1])) { puts("Correct password!"); return 0; }
    puts("Wrong password"); return 1;
}
'''


def compile_c(tmp_path, source: str, name: str = "prog", flags=()):
    need("gcc")
    src = tmp_path / f"{name}.c"
    src.write_text(source)
    out = tmp_path / name
    subprocess.run(["gcc", *flags, str(src), "-o", str(out)], check=True, capture_output=True)
    return out


def strip_binary(path):
    need("strip")
    out = path.with_name(path.name + "_stripped")
    subprocess.run(["strip", str(path), "-o", str(out)], check=True, capture_output=True)
    return out
