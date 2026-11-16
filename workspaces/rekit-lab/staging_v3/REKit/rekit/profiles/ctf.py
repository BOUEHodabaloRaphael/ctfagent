from __future__ import annotations

import re
from typing import Any

from ..core.binary import ParsedBinary
from ..core.carve import carve
from ..core.crypto import scan_crypto
from ..core.decoders import decode_candidates
from ..core.fileinfo import extract_strings
from ..core.iocs import extract_iocs
from ..core.models import Finding
from ..core.stackstrings import find_stack_strings
from ..core.xorscan import xor_scan
from ..core.xrefs import XrefIndex, find_main
from .common import cached, opt, protections_lines, where

FLAG_RE = re.compile(r"(?i)\b[a-z0-9_]{2,24}\{[^\r\n}]{3,160}\}")
KEYWORDS = ("flag", "ctf", "password", "passwd", "secret", "token", "license", "serial", "correct", "wrong",
            "success", "admin", "decrypt", "verify", "congrat", "invalid", "access", "denied", "granted", "key")
VERDICT_WORDS = ("correct", "wrong", "success", "fail", "invalid", "incorrect", "congrat", "granted", "denied",
                 "welcome", "try again", "nope", "flag", "good job", "valid")
VERDICT_RE = re.compile("|".join(map(re.escape, VERDICT_WORDS)), re.I)
UNSAFE_FUNCS = {
    "gets": "no bounds checking at all (always exploitable)", "strcpy": "unbounded copy", "strcat": "unbounded append",
    "sprintf": "unbounded formatted write", "vsprintf": "unbounded formatted write", "scanf": "%s without width overflows",
    "__isoc99_scanf": "%s without width overflows", "stpcpy": "unbounded copy", "getwd": "unbounded path write",
    "mktemp": "race-prone temp file", "tmpnam": "race-prone temp file", "system": "shell command execution",
    "popen": "shell command execution", "execve": "program execution", "read": "check length vs buffer size",
    "memcpy": "check length vs buffer size", "printf": "format-string risk if the format is user-controlled",
    "fprintf": "format-string risk if the format is user-controlled", "alloca": "stack allocation of attacker size",
}
KEYWORD_RE = re.compile("|".join(map(re.escape, KEYWORDS)), re.I)
INTERESTING_SYMS = re.compile(r"(?i)^(win|flag|get_?flag|print_?flag|shell|backdoor|secret|admin|debug|vuln|"
                              r"give_?shell|spawn_?shell|read_?flag|check|verify|validate|decrypt|encrypt|auth|login)\w*$")


def _flag_findings(strings, pb) -> tuple[list[Finding], list[str]]:
    flags = sorted({m.group(0) for s in strings for m in FLAG_RE.finditer(s["value"])})
    out: list[Finding] = []
    if flags:
        ev = [f"{where(pb, x['offset'])}: {x['value'][:200]}" for x in strings if any(f in x["value"] for f in flags)][:20]
        out.append(Finding("CTF-STR-001", "Flag-like strings found", "medium", "high",
                           "One or more strings match a common flag-shaped pattern. Verify whether each value is a real challenge flag.",
                           ev, ["A matching pattern can be a decoy or an example string."], "ctf"))
    return out, flags


def analyze_ctf(data: bytes, parsed: ParsedBinary | None = None, strings: list[dict[str, Any]] | None = None,
                options: dict[str, Any] | None = None) -> tuple[list[Finding], dict]:
    findings: list[Finding] = []
    errors: list[str] = []
    strings = strings if strings is not None else extract_strings(data, min_length=opt(options, "min_string", 4))
    values = [x["value"] for x in strings]

    flag_findings, flags = _flag_findings(strings, parsed)
    findings += flag_findings

    relevant = [x for x in strings if KEYWORD_RE.search(x["value"])]
    if relevant:
        findings.append(Finding("CTF-STR-002", "Challenge-relevant strings", "info", "medium",
                                "Strings may help locate validation logic, secrets, or success/failure paths.",
                                [f"{where(parsed, x['offset'])}: {x['value'][:180]}" for x in relevant[:40]],
                                ["Strings alone do not show how a value is used."], "ctf",
                                next_steps=["rekit xrefs <file> --string '<text>'  # find the code that uses a string"]))

    iocs = extract_iocs(data, include_noise=True, strings=strings)
    for kind, items in iocs.items():
        if items:
            findings.append(Finding(f"CTF-IOC-{kind.upper()}", f"Extracted {kind.upper()}", "info", "medium",
                                    f"Extracted {len(items)} {kind} value(s). These may be challenge infrastructure, test data, or decoys.",
                                    items[:100], ["Validate each value in context before acting on it."], "ctf"))

    try:
        decoded = decode_candidates(strings)
        if decoded:
            hits = [d for d in decoded if d.get("flags")]
            ev = [f"{where(parsed, d['offset'])} [{d['encoding']}] {d['source'][:50]} -> {d['preview'][:90]}" for d in decoded[:15]]
            findings.append(Finding("CTF-DEC-001", "Encoded data decodes to readable content" + (" (flag-like!)" if hits else ""),
                                    "medium" if hits else "info", "high" if hits else "low",
                                    "base64 / hex / reversed / ROT13 strings that decode to printable text, flags, or known file headers.",
                                    ev, ["Heuristic: random printable-looking base64 can decode by chance."], "ctf"))
    except Exception as exc:  # noqa: BLE001 - one broken analyzer must not abort the run
        errors.append(f"decoders: {type(exc).__name__}: {exc}")

    xor_res: list[dict[str, Any]] = []
    if opt(options, "xor", True):
        try:
            xor_res = cached(options, "xor", lambda: xor_scan(data, max_bytes=opt(options, "xor_max_bytes", 16 * 1024 * 1024)))
            if xor_res:
                flagged = [r for r in xor_res if r["flags"]]
                ev = []
                for r in xor_res[:6]:
                    ev.append(f"key {r['key_hex']}: {r['hits']} hit(s) " + (f"flags={r['flags']} " if r["flags"] else "") +
                              f"markers={list(r['markers'])[:4]} first@0x{r['offsets'][0]:x}")
                findings.append(Finding("CTF-XOR-001", "Single-byte XOR obfuscation detected", "medium" if flagged else "low",
                                        "high" if flagged else "medium",
                                        "Known plaintext (flag prefixes, URLs, shell paths, API names) appears when part of the file is XORed with one byte.",
                                        ev, ["Only a single repeating byte is searched; multi-byte keys are not covered."], "ctf",
                                        next_steps=[f"rekit xor <file> --key {xor_res[0]['key_hex']} --dump decoded.bin"]))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"xor: {type(exc).__name__}: {exc}")

    stack: list[dict[str, Any]] = []
    if parsed is None or parsed.arch in ("x86", "x86_64"):
        try:
            if parsed is not None:
                from ..core.xrefs import exec_ranges
                for lo, hi in exec_ranges(parsed, data):
                    stack += find_stack_strings(data, lo, hi)
            else:
                stack = find_stack_strings(data)
            if stack:
                has_flag = any(FLAG_RE.search(s["value"]) for s in stack)
                findings.append(Finding("CTF-STK-001", "Stack-built strings" + (" containing a flag-like value" if has_flag else ""),
                                        "medium" if has_flag else "info", "medium",
                                        "Strings assembled byte-by-byte on the stack with immediate moves; invisible to a plain `strings` run.",
                                        [f"{where(parsed, s['offset'])}: {s['value'][:120]}" for s in stack[:30]],
                                        ["Reconstructed from instruction patterns; ordering assumes ascending stack addresses."], "ctf"))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"stackstrings: {type(exc).__name__}: {exc}")

    crypto = []
    try:
        crypto = cached(options, "crypto", lambda: scan_crypto(data))
        if crypto:
            findings.append(Finding("CTF-CRYPTO-001", "Cryptographic constants present", "info", "medium",
                                    "Algorithm tables or initial values were found; the validation routine may hash or encrypt the input.",
                                    [f"{c['name']} ({c['confidence']}, {c['matched']}) first@{where(parsed, c['first_offset'])}" for c in crypto],
                                    ["Constants prove a table exists, not that it is used on the checked input."], "ctf"))
    except Exception as exc:  # noqa: BLE001
        errors.append(f"crypto: {type(exc).__name__}: {exc}")

    leads: list[dict[str, Any]] = []
    main_info = None
    if parsed is not None:
        findings.append(Finding("CTF-PROT-001", f"{parsed.format} {parsed.bits}-bit {parsed.arch}: protections", "info", "high",
                                "Hardening features that decide which exploitation techniques are viable.",
                                protections_lines(parsed), ["Derived from headers and symbols; stripped static binaries may hide canary/fortify."], "ctf"))
        imports = {i.get("name") for i in parsed.imports if i.get("name")} | {s.name for s in parsed.symbols if s.imported}
        unsafe = {n: UNSAFE_FUNCS[n] for n in imports if n in UNSAFE_FUNCS}
        if unsafe:
            sev = "medium" if {"gets", "strcpy", "sprintf", "scanf", "__isoc99_scanf", "strcat", "vsprintf"} & set(unsafe) else "low"
            findings.append(Finding("CTF-PWN-001", "Potentially unsafe libc functions imported", sev, "medium",
                                    "Common memory-corruption sinks are linked in. Whether they are reachable with attacker data needs code review.",
                                    [f"{n}: {why}" for n, why in sorted(unsafe.items())], ["Import presence is not proof of a vulnerability."], "ctf"))
        interesting = sorted({s.name for s in parsed.symbols if not s.imported and s.kind == "FUNC" and INTERESTING_SYMS.match(s.name)})
        if interesting:
            findings.append(Finding("CTF-SYM-001", "Interesting function names", "info", "medium",
                                    "Symbol names that often mark win functions or validation routines.",
                                    interesting[:40], ["Names can be misleading."], "ctf",
                                    next_steps=["rekit disasm <file> --symbol <name>"]))
        if parsed.arch in ("x86", "x86_64"):
            try:
                main_info = find_main(data, parsed)
                if main_info:
                    findings.append(Finding("CTF-MAIN-001", "main() located", "info", "medium",
                                            f"main is at 0x{main_info['address']:x} ({main_info['method']}). Entry point 0x{(parsed.entry or 0):x}.",
                                            [], [], "ctf", next_steps=[f"rekit disasm <file> --va 0x{main_info['address']:x} -n 60"]))
                if opt(options, "leads", True):
                    idx = XrefIndex(data, parsed)
                    seen_fn: set[int] = set()
                    for s in strings:
                        low = s["value"].lower()
                        if s["encoding"] != "ascii" or len(s["value"]) > 120 or not VERDICT_RE.search(s["value"]):
                            continue
                        va = parsed.offset_to_vaddr(s["offset"])
                        if va is None:
                            continue
                        refs = idx.refs(va)
                        for r in refs[:3]:
                            fn = r["function"]
                            leads.append({"string": s["value"], "string_va": va, "ref_va": r["vaddr"], "kind": r["kind"],
                                          "function": fn.get("name"), "function_va": fn.get("address")})
                            if fn.get("address") is not None:
                                seen_fn.add(fn["address"])
                        if len(leads) >= 40:
                            break
                    if leads:
                        findings.append(Finding("CTF-LEAD-001", "Code that references success/failure/flag strings", "medium", "medium",
                                                "These functions print verdict-like strings: the input validation logic is almost certainly in or just before them.",
                                                [f"'{l['string'][:60]}' <- {l['kind']} @0x{l['ref_va']:x} in {l['function'] or '?'}"
                                                 f"{'' if l['function_va'] is None else f' (0x{l['function_va']:x})'}" for l in leads[:25]],
                                                ["x86/x86-64 direct references only; strings loaded through tables or computed addresses are missed.",
                                                 "Function starts are guessed from prologues when symbols are absent."], "ctf",
                                                next_steps=[f"rekit disasm <file> --va 0x{sorted(seen_fn)[0]:x} -n 80" if seen_fn else
                                                            "rekit xrefs <file> --string '<text>'"]))
            except Exception as exc:  # noqa: BLE001
                errors.append(f"x86 analysis: {type(exc).__name__}: {exc}")

    embedded: list[dict[str, Any]] = []
    if opt(options, "carve", True):
        try:
            embedded = cached(options, "carve", lambda: carve(data))
            if embedded:
                findings.append(Finding("CTF-EMB-001", "Embedded files / compressed streams", "info", "medium",
                                        "Signatures of other file formats were found inside the file.",
                                        [f"0x{e['offset']:x}: {e['type']}" + (f" ({e['size']} bytes)" if e.get("size") else "") for e in embedded[:25]],
                                        ["Signature matches can be coincidental; PE/ELF/zlib entries are validated."], "ctf",
                                        next_steps=["rekit carve <file> --extract out/"]))
        except Exception as exc:  # noqa: BLE001
            errors.append(f"carve: {type(exc).__name__}: {exc}")

    details = {"strings_count": len(strings), "strings_preview": strings[:200], "flag_candidates": flags, "iocs": iocs,
               "xor": xor_res[:10], "stack_strings": stack[:100], "crypto": crypto, "leads": leads, "main": main_info,
               "embedded": embedded, "errors": errors}
    return findings, details
