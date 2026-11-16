"""Pure-Python PE/COFF parser (PE32 and PE32+)."""
from __future__ import annotations

import hashlib
import struct
from datetime import datetime, timezone

from .binary import ParsedBinary, ParseError, Section, Segment, cstr, unpack
from .util import entropy

MACHINES = {0x14C: ("x86", "x86", 32), 0x8664: ("x86_64", "x86-64", 64), 0x1C0: ("arm", "ARM", 32),
            0x1C4: ("arm", "ARM Thumb-2", 32), 0xAA64: ("aarch64", "ARM64", 64),
            0x200: ("ia64", "IA-64", 64), 0x166: ("mips", "MIPS R4000", 32)}
SUBSYSTEMS = {1: "native", 2: "windows GUI", 3: "windows console", 5: "OS/2", 7: "POSIX",
              9: "windows CE", 10: "EFI application", 11: "EFI boot driver", 14: "xbox"}
DLL_CHARS = {0x20: "high_entropy_va", 0x40: "aslr", 0x80: "force_integrity", 0x100: "dep",
             0x200: "no_isolation", 0x400: "no_seh", 0x800: "no_bind", 0x1000: "appcontainer",
             0x2000: "wdm_driver", 0x4000: "cfg", 0x8000: "terminal_server_aware"}
STANDARD_SECTIONS = {".text", ".data", ".rdata", ".bss", ".idata", ".edata", ".rsrc", ".reloc",
                     ".pdata", ".xdata", ".tls", ".crt", ".didat", ".gfids", ".00cfg", ".CRT",
                     ".debug", "CODE", "DATA", "BSS", ".sdata", ".ndata", ".orpc", ".detourc",
                     ".retplne", ".voltbl", "INIT", "PAGE", ".text$mn", ".code"}


def _flags(ch: int) -> str:
    return ("r" if ch & 0x40000000 else "-") + ("w" if ch & 0x80000000 else "-") + ("x" if ch & 0x20000000 else "-")


def pe_checksum(data: bytes, checksum_off: int) -> int:
    """Standard PE checksum (as computed by imagehlp)."""
    total = 0
    n = len(data)
    padded = data + (b"\x00" if n % 2 else b"")
    words = struct.unpack("<%dH" % (len(padded) // 2), padded)
    skip = checksum_off // 2
    for i, w in enumerate(words):
        if i in (skip, skip + 1):
            continue
        total += w
        total = (total & 0xFFFF) + (total >> 16)
    total = (total & 0xFFFF) + (total >> 16)
    return (total + n) & 0xFFFFFFFF


def imphash(imports: list[dict]) -> str | None:
    parts = []
    for imp in imports:
        lib = imp.get("lib", "").lower()
        for ext in (".dll", ".ocx", ".sys"):
            if lib.endswith(ext):
                lib = lib[: -len(ext)]
        fn = imp.get("name") or f"ord{imp.get('ordinal')}"
        parts.append(f"{lib}.{fn.lower()}")
    if not parts:
        return None
    return hashlib.md5(",".join(parts).encode(), usedforsecurity=False).hexdigest()


def parse_pe(data: bytes) -> ParsedBinary:
    if len(data) < 64 or data[:2] != b"MZ":
        raise ParseError("not a PE file (no MZ)")
    (lfanew,) = unpack("<I", data, 0x3C)
    if lfanew < 0x40 or lfanew + 24 > len(data) or data[lfanew:lfanew + 4] != b"PE\0\0":
        raise ParseError("MZ header without valid PE signature")
    machine, nsec, timestamp, _symptr, _nsym, optsize, characteristics = unpack("<HHIIIHH", data, lfanew + 4)
    opt = lfanew + 24
    (magic,) = unpack("<H", data, opt)
    if magic not in (0x10B, 0x20B):
        raise ParseError(f"unknown optional header magic 0x{magic:x}")
    plus = magic == 0x20B
    arch, mname, bits = MACHINES.get(machine, ("unknown", f"unknown(0x{machine:x})", 64 if plus else 32))
    (entry_rva,) = unpack("<I", data, opt + 16)
    if plus:
        (image_base,) = unpack("<Q", data, opt + 24)
        dd_off, nrva_off = opt + 112, opt + 108
    else:
        (image_base,) = unpack("<I", data, opt + 28)
        dd_off, nrva_off = opt + 96, opt + 92
    # explicit field reads (clear > clever)
    (sect_align, file_align) = unpack("<II", data, opt + 32)
    (size_image, size_headers, checksum) = unpack("<III", data, opt + 56)
    (subsystem, dll_chars) = unpack("<HH", data, opt + 68)
    (nrva,) = unpack("<I", data, nrva_off)
    nrva = min(nrva, 16)

    kind = "dll" if characteristics & 0x2000 else ("driver" if subsystem == 1 else "executable")
    pb = ParsedBinary(format="PE", bits=bits, endian="little", arch=arch, machine=mname, kind=kind,
                      entry=(image_base + entry_rva) if entry_rva else None, image_base=image_base,
                      file_size=len(data))
    pb.metadata.update(
        timestamp=timestamp, timestamp_utc=datetime.fromtimestamp(timestamp, timezone.utc).isoformat() if timestamp else None,
        subsystem=SUBSYSTEMS.get(subsystem, str(subsystem)), characteristics=characteristics,
        pe_plus=plus, header_checksum=checksum, size_of_image=size_image,
        section_alignment=sect_align, file_alignment=file_align)

    dirs: list[tuple[int, int]] = []
    for i in range(nrva):
        try:
            dirs.append(unpack("<II", data, dd_off + i * 8))
        except ParseError:
            break

    # ---- sections ----------------------------------------------------------------
    sec_off = opt + optsize
    for i in range(min(nsec, 96)):
        try:
            name_b, vsize, vaddr, rawsize, rawptr, _r, _l, _nr, _nl, ch = unpack("<8sIIIIIIHHI", data, sec_off + i * 40)
        except ParseError:
            pb.warnings.append("section table truncated")
            break
        name = name_b.split(b"\0")[0].decode("latin-1")
        sec = Section(name=name, offset=rawptr, size=rawsize, vaddr=image_base + vaddr,
                      vsize=vsize or rawsize, flags=_flags(ch), kind=hex(ch), index=i)
        if rawsize and rawptr + rawsize <= len(data):
            sec.entropy = entropy(data[rawptr:rawptr + rawsize])
        elif rawsize and rawptr < len(data):
            sec.entropy = entropy(data[rawptr:])
            pb.warnings.append(f"section {name!r} raw data extends past end of file")
        pb.sections.append(sec)
        if rawsize:
            pb.segments.append(Segment(vaddr=image_base + vaddr, vsize=max(vsize, rawsize),
                                       offset=rawptr, size=min(rawsize, max(vsize, rawsize)), flags=sec.flags, name=name))
    pb.segments.append(Segment(vaddr=image_base, vsize=size_headers, offset=0, size=min(size_headers, len(data)), flags="r--", name="headers"))

    def rva2off(rva: int):
        return pb.vaddr_to_offset(image_base + rva)

    def read_cstr_rva(rva: int, maxlen=512) -> str:
        off = rva2off(rva)
        return cstr(data, off, maxlen) if off is not None else ""

    # ---- imports -----------------------------------------------------------------
    ptr = 8 if plus else 4
    ord_flag = 1 << (63 if plus else 31)

    def read_thunks(rva: int, lib: str, bucket: list):
        off = rva2off(rva)
        if off is None:
            return
        for k in range(8192):
            try:
                (val,) = unpack("<Q" if plus else "<I", data, off + k * ptr)
            except ParseError:
                break
            if val == 0:
                break
            if val & ord_flag:
                bucket.append({"lib": lib, "name": None, "ordinal": val & 0xFFFF})
            else:
                o = rva2off(val & 0x7FFFFFFF)
                if o is None:
                    continue
                bucket.append({"lib": lib, "name": cstr(data, o + 2, 256), "hint": struct.unpack_from("<H", data, o)[0] if o + 2 <= len(data) else 0})

    if len(dirs) > 1 and dirs[1][0]:
        off = rva2off(dirs[1][0])
        if off is not None:
            for i in range(512):
                try:
                    oft, _ts, _fc, name_rva, ft = unpack("<IIIII", data, off + i * 20)
                except ParseError:
                    break
                if not (oft or name_rva or ft):
                    break
                lib = read_cstr_rva(name_rva, 256)
                read_thunks(oft or ft, lib, pb.imports)
    if len(dirs) > 13 and dirs[13][0]:
        off = rva2off(dirs[13][0])
        if off is not None:
            for i in range(256):
                try:
                    attrs, name_rva, _mod, _iat, int_rva = unpack("<IIIII", data, off + i * 32)
                except ParseError:
                    break
                if not name_rva:
                    break
                if not attrs & 1:  # VAs instead of RVAs
                    name_rva -= image_base
                    int_rva -= image_base
                lib = read_cstr_rva(name_rva, 256)
                tmp: list = []
                read_thunks(int_rva, lib, tmp)
                for t in tmp:
                    t["delayed"] = True
                pb.imports.extend(tmp)
    pb.metadata["imphash"] = imphash([i for i in pb.imports if not i.get("delayed")])

    # ---- exports ------------------------------------------------------------------
    if dirs and dirs[0][0]:
        off = rva2off(dirs[0][0])
        if off is not None:
            try:
                (_c, _t, _maj, _min, name_rva, base, nfunc, nnames, f_rva, n_rva, o_rva) = unpack("<IIHHIIIIIII", data, off)
                pb.metadata["export_dll_name"] = read_cstr_rva(name_rva)
                fo, no, oo = rva2off(f_rva), rva2off(n_rva), rva2off(o_rva)
                names: dict[int, str] = {}
                if no is not None and oo is not None:
                    for k in range(min(nnames, 20000)):
                        nrv = struct.unpack_from("<I", data, no + 4 * k)[0]
                        ordi = struct.unpack_from("<H", data, oo + 2 * k)[0]
                        names[ordi] = read_cstr_rva(nrv, 256)
                if fo is not None:
                    for k in range(min(nfunc, 20000)):
                        frva = struct.unpack_from("<I", data, fo + 4 * k)[0]
                        if frva:
                            pb.exports.append({"name": names.get(k), "ordinal": base + k, "address": image_base + frva})
            except (ParseError, struct.error):
                pb.warnings.append("export directory malformed")

    # ---- TLS callbacks, signature, debug, .NET ---------------------------------------
    if len(dirs) > 9 and dirs[9][0]:
        off = rva2off(dirs[9][0])
        try:
            cb_va = unpack("<Q", data, off + 24)[0] if plus else unpack("<I", data, off + 12)[0]
            cbo = pb.vaddr_to_offset(cb_va) if cb_va else None
            count = 0
            while cbo is not None and count < 64:
                v = unpack("<Q" if plus else "<I", data, cbo + count * ptr)[0]
                if not v:
                    break
                count += 1
            pb.metadata["tls_callbacks"] = count
        except (ParseError, TypeError):
            pb.warnings.append("TLS directory malformed")
    if len(dirs) > 4 and dirs[4][0]:
        pb.metadata["authenticode"] = {"offset": dirs[4][0], "size": dirs[4][1], "validated": False}
    if len(dirs) > 14 and dirs[14][0]:
        pb.metadata["dotnet"] = True
    if len(dirs) > 6 and dirs[6][0]:
        off = rva2off(dirs[6][0])
        try:
            for i in range(min(dirs[6][1] // 28, 16)):
                _c, _ts, _ma, _mi, dtype, _sz, _rva, ptr_raw = unpack("<IIHHIIII", data, off + 28 * i)
                if dtype == 2 and ptr_raw and data[ptr_raw:ptr_raw + 4] == b"RSDS":
                    pb.metadata["pdb_path"] = cstr(data, ptr_raw + 24, 512)
                    pb.metadata["pdb_guid"] = data[ptr_raw + 4:ptr_raw + 20].hex()
        except (ParseError, TypeError):
            pass
    if checksum:
        try:
            pb.metadata["checksum_valid"] = pe_checksum(data, opt + 64) == checksum
        except struct.error:
            pass

    # ---- protections & overlay ---------------------------------------------------------
    pb.protections = {name: bool(dll_chars & bit) for bit, name in DLL_CHARS.items()
                      if name in ("aslr", "dep", "high_entropy_va", "cfg", "force_integrity", "appcontainer")}
    pb.protections["safeseh_possible"] = not bool(dll_chars & 0x400) and not plus
    pb.protections["rwx_sections"] = sum(1 for s in pb.sections if s.writable and s.executable)
    end = max([s.offset + s.size for s in pb.sections] + [size_headers])
    if len(data) > end:
        size = len(data) - end
        sig = pb.metadata.get("authenticode")
        if sig and sig["offset"] >= end:
            size = max(0, sig["offset"] - end)
        if size:
            pb.overlay = {"offset": end, "size": size}
    return pb


def pe_anomalies(pb: ParsedBinary, data: bytes) -> list[tuple[str, str, str, str]]:
    """Return (id, title, detail, severity) for structural oddities."""
    out: list[tuple[str, str, str, str]] = []
    if pb.protections.get("rwx_sections"):
        names = [s.name for s in pb.sections if s.writable and s.executable]
        out.append(("PE-RWX", "Writable and executable section(s)", ", ".join(names), "medium"))
    ep_sec = pb.section_for_vaddr(pb.entry) if pb.entry else None
    if pb.entry and ep_sec is None:
        out.append(("PE-EP-OUTSIDE", "Entry point outside all sections", f"EP=0x{pb.entry:x}", "medium"))
    elif ep_sec is not None and (ep_sec is pb.sections[-1] and len(pb.sections) > 1 or not ep_sec.executable):
        out.append(("PE-EP-ODD", "Entry point in last or non-executable section", f"EP in {ep_sec.name!r}", "medium"))
    odd = [s.name for s in pb.sections if s.name not in STANDARD_SECTIONS]
    if odd:
        out.append(("PE-ODD-SECT", "Non-standard section names", ", ".join(odd[:20]), "low"))
    for s in pb.sections:
        if s.size == 0 and s.vsize > 0x1000 and s.executable:
            out.append(("PE-VIRT-ONLY", f"Executable section {s.name!r} has no raw data",
                        f"vsize={s.vsize} raw=0: space reserved for an unpacker", "medium"))
        if s.size and s.vsize > s.size * 10 and s.vsize > 0x10000 and s.name not in (".bss", ".data"):
            out.append(("PE-VSIZE", f"Section {s.name!r} virtual size >> raw size", f"vsize={s.vsize} raw={s.size}", "low"))
    ts = pb.metadata.get("timestamp")
    if ts:
        if ts > datetime.now(timezone.utc).timestamp() + 86400:
            out.append(("PE-TS-FUTURE", "Compile timestamp in the future", pb.metadata["timestamp_utc"], "low"))
    if pb.metadata.get("checksum_valid") is False and pb.metadata.get("header_checksum"):
        out.append(("PE-CHECKSUM", "Header checksum does not match file", "Seen on patched or modified files.", "low"))
    if pb.metadata.get("tls_callbacks"):
        out.append(("PE-TLS", "TLS callbacks present", f"{pb.metadata['tls_callbacks']} callback(s) run before the entry point (anti-debug / early code).", "low"))
    if pb.overlay and pb.overlay["size"] > 0:
        out.append(("PE-OVERLAY", "Overlay data after the last section",
                    f"{pb.overlay['size']} bytes at 0x{pb.overlay['offset']:x} (installers, appended payloads, or signatures).", "info"))
    return out
