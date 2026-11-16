from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path

from . import __version__
from .core.binary import ParsedBinary
from .core.carve import carve
from .core.diff import diff_files
from .core.disasm import HAS_CAPSTONE, disassemble
from .core.fileinfo import DEFAULT_MAX_SIZE, extract_strings, inspect_file
from .core.formats import parse_binary
from .core.iocs import iter_iocs
from .core.packers import detect_packers
from .core.patch import PatchError, PatchOp, apply_patches, invert_branch, nop_bytes, parse_hex, resolve_offset
from .core.reporting import print_console, write_html, write_json, write_markdown
from .core.util import hexdump, parse_int
from .core.xorscan import xor_decode, xor_scan
from .core.xrefs import XrefIndex, find_main
from .engine import PROFILES, analyze

COMMANDS = ("analyze", "strings", "hexdump", "find", "disasm", "xrefs", "xor", "carve", "patch", "unpack", "diff", "r2", "ghidra", "version")
FORMATS = ("console", "json", "markdown", "html", "both", "all")


def _load(path: str, max_size: int = DEFAULT_MAX_SIZE):
    data, info = inspect_file(path, max_size)
    pb, err = parse_binary(data)
    return data, info, pb, err


def _where(pb: ParsedBinary | None, off: int) -> str:
    if pb is None:
        return f"0x{off:08x}"
    sec, va = pb.section_for_offset(off), pb.offset_to_vaddr(off)
    return f"0x{off:08x}" + (f"  va=0x{va:x}" if va is not None else "") + (f"  [{sec.name}]" if sec else "")


def _resolve_location(args, pb: ParsedBinary | None, data: bytes) -> tuple[int, int | None]:
    """Return (file_offset, vaddr) from --at/--va/--entry/--main/--symbol."""
    if getattr(args, "symbol", None):
        if pb is None:
            raise SystemExit("--symbol needs a recognised ELF/PE/Mach-O file")
        sym = pb.symbol_by_name(args.symbol)
        if sym is None:
            exp = next((e for e in pb.exports if e.get("name") == args.symbol), None)
            if exp is None:
                raise SystemExit(f"symbol {args.symbol!r} not found (stripped binary? try --main or --va)")
            va = exp["address"]
        else:
            va = sym.value
        off = pb.vaddr_to_offset(va)
        if off is None:
            raise SystemExit(f"symbol {args.symbol} (0x{va:x}) is not backed by file data")
        return off, va
    if getattr(args, "main", False):
        if pb is None:
            raise SystemExit("--main needs a recognised ELF file")
        m = find_main(data, pb)
        if not m:
            raise SystemExit("could not locate main() (non-glibc start-up code or unsupported architecture); use --va")
        return pb.vaddr_to_offset(m["address"]), m["address"]
    if getattr(args, "entry", False):
        if pb is None or pb.entry is None or pb.entry_offset is None:
            raise SystemExit("no entry point available")
        return pb.entry_offset, pb.entry
    if getattr(args, "va", None) is not None:
        va = parse_int(args.va)
        if pb is None or pb.vaddr_to_offset(va) is None:
            raise SystemExit(f"virtual address 0x{va:x} is not backed by file data")
        return pb.vaddr_to_offset(va), va
    off = parse_int(args.at) if getattr(args, "at", None) is not None else 0
    return off, (pb.offset_to_vaddr(off) if pb else None)


def _add_target(p):
    p.add_argument("target", help="file to inspect")
    p.add_argument("--max-size", type=int, default=DEFAULT_MAX_SIZE, help="refuse files larger than this many bytes")


def _add_location(p, default_entry=False):
    g = p.add_mutually_exclusive_group()
    g.add_argument("--at", help="file offset (e.g. 0x1a40)")
    g.add_argument("--va", help="virtual address (e.g. 0x401136)")
    g.add_argument("--symbol", help="symbol / export name")
    g.add_argument("--main", action="store_true", help="main(); recovered from _start when stripped")
    g.add_argument("--entry", action="store_true", help="entry point")


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(prog="rekit", description="REKit: CTF reverse-engineering and static malware triage toolkit.",
                                 epilog="Run 'rekit <command> -h' for details. 'rekit FILE' is shorthand for 'rekit analyze FILE'.")
    ap.add_argument("--version", action="version", version=f"REKit {__version__}")
    sub = ap.add_subparsers(dest="command")

    a = sub.add_parser("analyze", help="full static triage with findings and reports")
    _add_target(a)
    a.add_argument("--profile", choices=PROFILES, default="both")
    a.add_argument("--format", default="console", help="comma list of: " + ", ".join(FORMATS) + " (both=json+markdown, all=json+markdown+html)")
    a.add_argument("--out", default="rekit-report", help="output path without extension (directories are created)")
    a.add_argument("--yara-rules", help="YARA rules file or directory (needs yara-python)")
    a.add_argument("--min-string", type=int, default=4)
    a.add_argument("--no-xor", action="store_true", help="skip the single-byte XOR scan")
    a.add_argument("--no-leads", action="store_true", help="skip success/failure-string xref analysis")
    a.add_argument("--no-carve", action="store_true", help="skip embedded-file detection")
    a.add_argument("--include-noise", action="store_true", help="keep private IPs / schema URLs in malware IOC output")
    a.add_argument("--no-defang", action="store_true", help="do not defang indicators in console/markdown/html")
    a.add_argument("-v", "--verbose", action="store_true")

    s = sub.add_parser("strings", help="extract strings with offsets, addresses and sections")
    _add_target(s)
    s.add_argument("-n", "--min-length", type=int, default=4)
    s.add_argument("-e", "--encoding", choices=("ascii", "utf-16le", "utf-16be", "all"), default="all")
    s.add_argument("--grep", help="regex filter (case-insensitive)")
    s.add_argument("--section", help="only strings located in this section")
    s.add_argument("--iocs", action="store_true", help="only strings that contain indicators")
    s.add_argument("--sort", choices=("offset", "length"), default="offset")

    h = sub.add_parser("hexdump", help="hex dump at an offset or address")
    _add_target(h)
    _add_location(h)
    h.add_argument("-n", "--length", type=int, default=256)

    f = sub.add_parser("find", help="search bytes (with ?? wildcards), text or regex")
    _add_target(f)
    g = f.add_mutually_exclusive_group(required=True)
    g.add_argument("--hex", help='byte pattern, e.g. "48 8d 3d ?? ?? ?? ??"')
    g.add_argument("--text", help="ASCII text (also tried as UTF-16LE)")
    g.add_argument("--regex", help="bytes regex")
    f.add_argument("--max", type=int, default=100)
    f.add_argument("-C", "--context", type=int, default=8, help="bytes of context to show")

    d = sub.add_parser("disasm", help="disassemble (Capstone, or objdump as fallback)")
    _add_target(d)
    _add_location(d)
    d.add_argument("-n", "--count", type=int, default=40)
    d.add_argument("--arch", help="override architecture (x86, x86_64, arm, aarch64, mips, ppc, ...)")
    d.add_argument("--mode", choices=("arm", "thumb"), help="ARM instruction set")

    x = sub.add_parser("xrefs", help="find code that references a string, address, or function (x86/x86-64)")
    _add_target(x)
    g = x.add_mutually_exclusive_group(required=True)
    g.add_argument("--string", help="text to locate; every occurrence is resolved")
    g.add_argument("--va", help="virtual address")
    g.add_argument("--symbol", help="function or data symbol")

    o = sub.add_parser("xor", help="single-byte XOR scan / decode")
    _add_target(o)
    o.add_argument("--key", help="decode with this key (0x22 or 34)")
    o.add_argument("--dump", help="write the decoded buffer to this file")
    o.add_argument("--start", default="0")
    o.add_argument("--end")
    o.add_argument("--known", action="append", default=[], help="extra known plaintext (>=6 bytes) to hunt for; repeatable")

    c = sub.add_parser("carve", help="locate (and extract) embedded files")
    _add_target(c)
    c.add_argument("--extract", metavar="DIR")

    pa = sub.add_parser("patch", help="patch bytes / NOP out / invert a conditional jump (writes a copy by default)")
    _add_target(pa)
    pa.add_argument("--bytes", nargs="+", action="append", default=[], metavar=("OFFSET", "HEX"), help="OFFSET NEWHEX [EXPECTHEX]")
    pa.add_argument("--nop", nargs="+", action="append", default=[], metavar=("OFFSET", "LENGTH"), help="OFFSET LENGTH [EXPECTHEX]")
    pa.add_argument("--invert", nargs="+", action="append", default=[], metavar="OFFSET", help="OFFSET [EXPECTHEX]  flip a conditional branch")
    pa.add_argument("--va", action="store_true", help="treat every OFFSET as a virtual address")
    pa.add_argument("--mode", choices=("arm", "thumb"), help="ARM instruction set for --nop/--invert")
    pa.add_argument("--out", help="output file (default: <file>.patched)")
    pa.add_argument("--in-place", action="store_true", help="modify the file itself (a .bak copy is kept)")
    pa.add_argument("--dry-run", action="store_true")
    pa.add_argument("--force", action="store_true", help="ignore EXPECT mismatches")
    pa.add_argument("--fix-pe-checksum", action="store_true")

    u = sub.add_parser("unpack", help="unpack UPX-packed executables (needs the upx tool)")
    _add_target(u)
    u.add_argument("-o", "--out")

    df = sub.add_parser("diff", help="compare two files")
    df.add_argument("a")
    df.add_argument("b")
    df.add_argument("--json", action="store_true")
    r2 = sub.add_parser("r2", help="radare2 summary: functions, interesting strings, main (needs radare2; use an isolated VM for malware)")
    _add_target(r2)
    r2.add_argument("--timeout", type=int, default=180)
    gh = sub.add_parser("ghidra", help="decompile with Ghidra headless (needs analyzeHeadless; use an isolated VM for malware)")
    _add_target(gh)
    gh.add_argument("-o", "--out")
    gh.add_argument("--timeout", type=int, default=600)
    sub.add_parser("version", help="print version")
    return ap


def cmd_analyze(args) -> int:
    formats: list[str] = []
    for part in args.format.split(","):
        part = part.strip().lower()
        if part not in FORMATS:
            raise SystemExit(f"unknown format {part!r}; choose from {', '.join(FORMATS)}")
        formats += {"both": ["json", "markdown"], "all": ["json", "markdown", "html"]}.get(part, [part])
    options = {"min_string": args.min_string, "xor": not args.no_xor, "leads": not args.no_leads, "carve": not args.no_carve,
               "include_noise": args.include_noise, "max_size": args.max_size}
    report = analyze(args.target, args.profile, args.yara_rules, options)
    base = Path(args.out)
    written = []
    for fmt in dict.fromkeys(formats):
        if fmt == "console":
            print_console(report, verbose=args.verbose, defang_iocs=not args.no_defang)
        elif fmt == "json":
            write_json(report, base.with_suffix(".json")); written.append(base.with_suffix(".json"))
        elif fmt == "markdown":
            write_markdown(report, base.with_suffix(".md"), not args.no_defang); written.append(base.with_suffix(".md"))
        elif fmt == "html":
            write_html(report, base.with_suffix(".html"), not args.no_defang); written.append(base.with_suffix(".html"))
    for w in written:
        print(f"wrote {w}", file=sys.stderr)
    return 0


def cmd_strings(args) -> int:
    data, _info, pb, _ = _load(args.target, args.max_size)
    encs = ("ascii", "utf-16le", "utf-16be") if args.encoding == "all" else (args.encoding,)
    items = extract_strings(data, args.min_length, 10**9, encs)
    pat = re.compile(args.grep, re.I) if args.grep else None
    if args.iocs:
        keep = {off for _k, _v, off, tags in iter_iocs(items) if "noise" not in tags}
        items = [i for i in items if i["offset"] in keep]
    n = 0
    if args.sort == "length":
        items.sort(key=lambda i: -len(i["value"]))
    for it in items:
        sec = pb.section_for_offset(it["offset"]) if pb else None
        if args.section and (not sec or sec.name != args.section):
            continue
        if pat and not pat.search(it["value"]):
            continue
        va = pb.offset_to_vaddr(it["offset"]) if pb else None
        tag = {"ascii": "a", "utf-16le": "w", "utf-16be": "W"}[it["encoding"]]
        print(f"{it['offset']:08x} {('0x%x' % va) if va is not None else '-':>12} {sec.name if sec else '-':<14} {tag} {it['value']}")
        n += 1
    print(f"# {n} string(s)", file=sys.stderr)
    return 0


def cmd_hexdump(args) -> int:
    data, _i, pb, _ = _load(args.target, args.max_size)
    off, va = _resolve_location(args, pb, data)
    print(hexdump(data[off:off + args.length], base=va if va is not None else off))
    return 0


def cmd_find(args) -> int:
    data, _i, pb, _ = _load(args.target, args.max_size)
    if args.hex:
        toks = args.hex.replace("0x", "").split()
        if len(toks) == 1 and len(toks[0]) > 2:
            toks = [toks[0][i:i + 2] for i in range(0, len(toks[0]), 2)]
        try:
            pattern = b"".join(b"." if t in ("??", "?") else re.escape(bytes.fromhex(t)) for t in toks)
        except ValueError:
            raise SystemExit("invalid --hex pattern (use hex bytes and ?? wildcards)")
        pats = [re.compile(pattern, re.S)]
    elif args.text:
        t = args.text.encode()
        pats = [re.compile(re.escape(t)), re.compile(re.escape(args.text.encode("utf-16le")))]
    else:
        pats = [re.compile(args.regex.encode(), re.S)]
    seen = 0
    for pat in pats:
        for m in pat.finditer(data):
            ctx = data[m.start():m.end() + args.context]
            print(f"{_where(pb, m.start())}  {ctx.hex(' ')}")
            seen += 1
            if seen >= args.max:
                print(f"# stopped after {args.max} matches", file=sys.stderr)
                return 0
    print(f"# {seen} match(es)", file=sys.stderr)
    return 0 if seen else 1


def cmd_disasm(args) -> int:
    data, _i, pb, _ = _load(args.target, args.max_size)
    if not any([args.at, args.va, args.symbol, args.main, args.entry]):
        args.entry = True
    off, va = _resolve_location(args, pb, data)
    try:
        res = disassemble(data, pb, off, va, args.count, args.arch, args.mode)
    except (RuntimeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    sym = pb.symbol_at(va) if (pb and va is not None) else None
    print(f"# engine={res['engine']} arch={res['arch']}" + (f"  {sym.name}" if sym else ""))
    for ins in res["instructions"]:
        print(f"{ins['address']:#010x}  {ins['bytes']:<24} {ins['mnemonic']:<8} {ins['operands']}")
    return 0


def cmd_xrefs(args) -> int:
    data, _i, pb, _ = _load(args.target, args.max_size)
    if pb is None:
        raise SystemExit("xrefs needs a recognised ELF/PE/Mach-O file")
    targets: list[tuple[str, int]] = []
    if args.string:
        needle = args.string.encode()
        pos = 0
        while (i := data.find(needle, pos)) != -1:
            va = pb.offset_to_vaddr(i)
            if va is not None:
                targets.append((f"string at 0x{i:x}", va))
            pos = i + 1
        wide = args.string.encode("utf-16le")
        pos = 0
        while (i := data.find(wide, pos)) != -1:
            va = pb.offset_to_vaddr(i)
            if va is not None:
                targets.append((f"wide string at 0x{i:x}", va))
            pos = i + 1
        if not targets:
            raise SystemExit("string not found in file-backed data")
    elif args.va:
        targets.append(("address", parse_int(args.va)))
    else:
        sym = pb.symbol_by_name(args.symbol)
        if not sym:
            raise SystemExit(f"symbol {args.symbol!r} not found")
        targets.append((f"symbol {args.symbol}", sym.value))
    try:
        idx = XrefIndex(data, pb)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    total = 0
    for label, va in targets:
        refs = idx.refs(va)
        print(f"{label}  va=0x{va:x}  -> {len(refs)} reference(s)")
        for r in refs:
            fn = r["function"]
            fname = f"{fn['name']} (0x{fn['address']:x}, {fn['method']})" if fn.get("address") is not None else (fn.get("name") or "?")
            print(f"   0x{r['vaddr']:x}  {r['kind']:<10} in {fname}")
            total += 1
    return 0 if total else 1


def cmd_xor(args) -> int:
    data, *_ = _load(args.target, args.max_size)
    if args.key is not None:
        key = parse_int(args.key)
        if not 0 <= key <= 255:
            raise SystemExit("key must be 0..255")
        dec = xor_decode(data, key, parse_int(args.start), parse_int(args.end) if args.end else None)
        if args.dump:
            Path(args.dump).write_bytes(dec)
            print(f"wrote {len(dec)} bytes to {args.dump}")
        else:
            sys.stdout.write(re.sub(r"[^\x20-\x7e\n]", ".", dec[:4096].decode("latin-1")) + "\n")
        return 0
    res = xor_scan(data, extra=[k.encode() for k in args.known])
    if not res:
        print("no single-byte XOR keys revealed known plaintext")
        return 1
    for r in res[:10]:
        print(f"key {r['key_hex']}  hits={r['hits']}  markers={dict(list(r['markers'].items())[:5])}  flags={r['flags']}")
        for smp in r["samples"][:3]:
            print(f"    @0x{smp['offset']:x}: {smp['text'][:100]}")
    return 0


def cmd_carve(args) -> int:
    data, _i, pb, _ = _load(args.target, args.max_size)
    found = carve(data)
    if not found:
        print("no embedded files found")
        return 1
    out = Path(args.extract) if args.extract else None
    if out:
        out.mkdir(parents=True, exist_ok=True)
    ends = [f["offset"] for f in found] + [len(data)]
    for n, f in enumerate(found):
        size = f.get("size") or (ends[n + 1] - f["offset"])
        print(f"0x{f['offset']:08x}  {f['type']:<12} {size if f.get('size') else '~' + str(size)} bytes  {f.get('note', '')}")
        if out:
            blob = data[f["offset"]:f["offset"] + size]
            if f["type"] == "zlib stream":
                import zlib
                try:
                    blob = zlib.decompressobj().decompress(blob)
                except zlib.error:
                    pass
            ext = {"PE": "exe", "ELF": "elf", "ZIP": "zip", "GZIP": "gz", "PDF": "pdf", "zlib stream": "bin"}.get(f["type"], "bin")
            (out / f"carved_{f['offset']:08x}.{ext}").write_bytes(blob)
    if out:
        print(f"extracted to {out}/")
    return 0


def cmd_patch(args) -> int:
    data, _i, pb, _ = _load(args.target, args.max_size)
    arch = pb.arch if pb else "x86_64"
    endian = pb.endian if pb else "little"
    ops: list[PatchOp] = []
    try:
        for spec in args.bytes:
            if len(spec) < 2:
                raise PatchError("--bytes needs OFFSET NEWHEX [EXPECTHEX]")
            off = resolve_offset(pb, parse_int(spec[0]), args.va)
            ops.append(PatchOp(off, parse_hex(spec[1]), parse_hex(spec[2]) if len(spec) > 2 else None, f"write {spec[1]}"))
        for spec in args.nop:
            if len(spec) < 2:
                raise PatchError("--nop needs OFFSET LENGTH [EXPECTHEX]")
            off = resolve_offset(pb, parse_int(spec[0]), args.va)
            ops.append(PatchOp(off, nop_bytes(arch, parse_int(spec[1]), endian, args.mode), parse_hex(spec[2]) if len(spec) > 2 else None, f"NOP x{spec[1]}"))
        for spec in args.invert:
            off = resolve_offset(pb, parse_int(spec[0]), args.va)
            old, new, desc = invert_branch(data, off, arch, endian, args.mode)
            ops.append(PatchOp(off, new, parse_hex(spec[1]) if len(spec) > 1 else old, desc))
        if not ops:
            raise PatchError("nothing to do: give --bytes, --nop or --invert")
        res = apply_patches(args.target, ops, args.out, args.in_place, args.dry_run, args.force, args.fix_pe_checksum)
    except PatchError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    for ch in res["changes"]:
        va = pb.offset_to_vaddr(ch["offset"]) if pb else None
        print(f"0x{ch['offset']:x}" + (f" (va 0x{va:x})" if va is not None else "") + f": {ch['old']} -> {ch['new']}  {ch['description']}")
    if res.get("pe_checksum") is not None:
        print(f"PE checksum updated to 0x{res['pe_checksum']:08x}")
    print("dry run: no file written" if res["dry_run"] else f"wrote {res['output']}" + (f" (backup: {res['backup']})" if res.get("backup") else ""))
    return 0


def cmd_unpack(args) -> int:
    data, _i, pb, _ = _load(args.target, args.max_size)
    pk = detect_packers(data, pb)
    upx = [d for d in pk["detections"] if d["name"] == "UPX"]
    if not upx:
        print("no UPX packing detected (REKit only unpacks UPX; other packers need dedicated tools or dynamic unpacking)")
        return 1
    exe = shutil.which("upx")
    if not exe:
        print("UPX detected but the 'upx' tool is not installed (https://upx.github.io/)", file=sys.stderr)
        return 2
    out = args.out or str(Path(args.target).with_name(Path(args.target).name + ".unpacked"))
    proc = subprocess.run([exe, "-d", "-o", out, args.target], capture_output=True, text=True, timeout=300, check=False)
    sys.stdout.write(proc.stdout)
    if proc.returncode != 0:
        print(proc.stderr.strip(), file=sys.stderr)
        return 2
    print(f"unpacked to {out}")
    return 0


def cmd_diff(args) -> int:
    a, b = Path(args.a).read_bytes(), Path(args.b).read_bytes()
    res = diff_files(a, b)
    if args.json:
        import json
        print(json.dumps(res, indent=2, default=str))
        return 0
    print("IDENTICAL" if res["identical"] else f"DIFFERENT  size {res['size']['a']} -> {res['size']['b']}")
    if res.get("note"):
        print(res["note"])
    for r in res["byte_ranges"][:50]:
        extra = (f" va=0x{r['vaddr']:x}" if "vaddr" in r else "") + (f" [{r['section']}]" if "section" in r else "")
        print(f"  0x{r['offset']:x} +{r['length']}{extra}: {r['a']} -> {r['b']}")
    for k in ("added", "removed", "changed"):
        if res["sections"][k]:
            print(f"sections {k}: {', '.join(res['sections'][k])}")
    for k in ("added", "removed"):
        if res["imports"][k]:
            print(f"imports {k}: {', '.join(res['imports'][k][:30])}")
    st = res["strings"]
    print(f"strings: +{st['added_total']} / -{st['removed_total']}")
    for s in st["added"][:15]:
        print(f"  + {s[:100]}")
    for s in st["removed"][:15]:
        print(f"  - {s[:100]}")
    for k, v in res["metadata"].items():
        print(f"metadata {k}: {v['a']} -> {v['b']}")
    return 0 if res["identical"] else 1


def cmd_r2(args) -> int:
    from .core.integrations import ToolMissing, r2_summary
    try:
        res = r2_summary(args.target, args.timeout)
    except ToolMissing as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except (RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"functions: {res['function_count']}")
    for f in res["functions"][:30]:
        addr = f["address"] if f["address"] is not None else 0
        print(f"  0x{addr:08x}  {f['name']}  ({f['size']} bytes)")
    for s in res["interesting_strings"][:15]:
        print(f"  string 0x{(s['address'] or 0):x}: {s['value']}")
    if res["main_disassembly"]:
        print("--- main ---")
        print("\n".join(res["main_disassembly"]))
    return 0


def cmd_ghidra(args) -> int:
    from .core.integrations import ToolMissing, ghidra_decompile
    try:
        res = ghidra_decompile(args.target, args.out, args.timeout)
    except ToolMissing as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except (RuntimeError, subprocess.TimeoutExpired) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(f"decompiled {res['functions']} function(s) to {res['output']}")
    return 0


HANDLERS = {"r2": cmd_r2, "ghidra": cmd_ghidra, "analyze": cmd_analyze, "strings": cmd_strings, "hexdump": cmd_hexdump, "find": cmd_find, "disasm": cmd_disasm,
            "xrefs": cmd_xrefs, "xor": cmd_xor, "carve": cmd_carve, "patch": cmd_patch, "unpack": cmd_unpack, "diff": cmd_diff}


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] not in COMMANDS and not argv[0].startswith("-"):
        argv.insert(0, "analyze")          # `rekit FILE` shorthand (v3.0 compatible)
    elif argv and argv[0] in ("--profile", "--format", "--out"):
        argv.insert(0, "analyze")
    ap = build_parser()
    args = ap.parse_args(argv)
    if not args.command:
        ap.print_help()
        return 0
    if args.command == "version":
        print(f"REKit {__version__}" + ("  (capstone available)" if HAS_CAPSTONE else "  (capstone not installed; objdump fallback)"))
        return 0
    try:
        return HANDLERS[args.command](args)
    except (FileNotFoundError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    except BrokenPipeError:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
