from __future__ import annotations

import time
from collections import Counter
from pathlib import Path
from typing import Any

from . import __version__
from .core.elf import analyze_elf
from .core.fileinfo import DEFAULT_MAX_SIZE, extract_strings, inspect_file
from .core.formats import parse_binary
from .core.models import SEVERITIES, SEVERITY_RANK, AnalysisReport
from .profiles.ctf import analyze_ctf
from .profiles.malware import analyze_malware_static

PROFILES = ("ctf", "malware", "both")


def _summarise(report: AnalysisReport) -> dict[str, Any]:
    counts = Counter(f.severity for f in report.findings)
    ordered = sorted(report.findings, key=lambda f: (-SEVERITY_RANK.get(f.severity, 0), f.id))
    steps: list[str] = []
    for f in ordered:
        for s in f.next_steps:
            if not any(s.split(" -n")[0] == t.split(" -n")[0] for t in steps):
                steps.append(s)
    return {"findings_by_severity": {s: counts.get(s, 0) for s in reversed(SEVERITIES)},
            "top_findings": [{"id": f.id, "severity": f.severity, "title": f.title} for f in ordered[:8]],
            "suggested_next_steps": steps[:8],
            "note": "Counts and ordering are triage aids; REKit never emits a malicious/benign verdict."}


def analyze(path: str | Path, profile: str = "both", yara_rules: str | None = None,
            options: dict[str, Any] | None = None) -> dict:
    """Analyse ``path`` statically and return the JSON-serialisable report dictionary."""
    if profile not in PROFILES:
        raise ValueError(f"Unsupported profile: {profile}")
    options = dict(options or {})
    t0 = time.perf_counter()
    timings: dict[str, float] = {}

    def timed(name: str, fn, *a, **kw):
        t = time.perf_counter()
        try:
            return fn(*a, **kw)
        finally:
            timings[name] = round((time.perf_counter() - t) * 1000, 1)

    data, info = timed("read+hash", inspect_file, path, options.get("max_size", DEFAULT_MAX_SIZE))
    report = AnalysisReport(tool="REKit", version=__version__, profile=profile, target=str(Path(path).resolve()), file=info)
    parsed, parse_err = timed("parse", parse_binary, data)
    if parse_err:
        report.errors.append(f"format parser: {parse_err}")
    if parsed is not None:
        info["format"] = f"{parsed.format} {parsed.bits}-bit {parsed.arch} ({parsed.kind})"
        report.modules["binary"] = parsed.to_dict()
        if parsed.format == "ELF":
            report.modules["elf"] = analyze_elf(path, data)
    else:
        report.modules["binary"] = None
        report.modules["elf"] = {"is_elf": False, "available": False}
    report.modules["static_analysis"] = True
    strings = timed("strings", extract_strings, data, options.get("min_string", 4))
    report.modules["strings"] = {"count": len(strings)}
    if info["size_bytes"] > 32 * 1024 * 1024:
        report.limitations.append("Crypto-constant search is limited to the first 32 MiB and the XOR scan to the first 16 MiB of this large file.")
    report.limitations.extend([
        "Static triage only; the target is never executed.",
        "No malware/benign verdict is produced automatically.",
        "Disassembly-based analysis (xrefs, stack strings, main discovery) covers x86/x86-64 only; other architectures rely on headers, symbols and strings.",
    ])
    if parsed is None and info["type"] in ("ELF", "PE/DOS") or (parsed is None and info["type"].startswith("Mach-O")):
        report.limitations.append("The file looks like an executable but its headers could not be parsed; results rely on raw bytes only.")
    if profile in ("ctf", "both"):
        findings, details = timed("ctf", analyze_ctf, data, parsed, strings, options)
        if profile == "both":  # the malware profile reports noise-filtered IOCs; avoid listing them twice
            findings = [f for f in findings if not f.id.startswith("CTF-IOC-")]
        report.findings.extend(findings)
        report.modules["ctf"] = details
        report.errors.extend(details.get("errors", []))
    if profile in ("malware", "both"):
        findings, details = timed("malware", analyze_malware_static, data, info, report.modules.get("elf"), yara_rules, parsed, strings, options)
        seen = {f.id for f in report.findings}
        report.findings.extend(f for f in findings if f.id not in seen)
        report.modules["malware"] = details
        report.errors.extend(details.get("errors", []))
    report.findings.sort(key=lambda f: -SEVERITY_RANK.get(f.severity, 0))
    timings["total"] = round((time.perf_counter() - t0) * 1000, 1)
    report.modules["timings_ms"] = timings
    report.summary = _summarise(report)
    return report.to_dict()
