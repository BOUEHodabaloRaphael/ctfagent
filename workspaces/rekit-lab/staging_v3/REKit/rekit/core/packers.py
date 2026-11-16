"""Packer / protector / toolchain recognition and packing indicators.

Section names alone are trivially renamed, so every verdict carries its evidence and a
confidence level. UPX detection requires structure (section names, header position or the
``$Info`` banner) rather than a stray ``UPX!`` string anywhere in the file (v2.1 bug 7).
"""
from __future__ import annotations

from typing import Any

from .binary import ParsedBinary

PE_SECTION_SIGS = {
    "UPX": ("UPX0", "UPX1", "UPX2", "UPX!"), "MPRESS": (".MPRESS1", ".MPRESS2"),
    "ASPack": (".aspack", ".adata"), "PECompact": ("PEC2", "pec1", "pec2", "PECompact2"),
    "FSG": ("FSG!",), "Themida / WinLicense": (".themida", ".winlice", ".Themida"),
    "VMProtect": (".vmp0", ".vmp1", ".vmp2"), "Enigma Protector": (".enigma1", ".enigma2"),
    "Petite": (".petite",), "NsPack": (".nsp0", ".nsp1", ".nsp2", "nsp0", "nsp1"),
    "Obsidium": (".obsidiu",), "ASProtect": (".aspr",), "kkrunchy": ("kkrunchy",),
    "Armadillo": (".data1",), "tElock": (".tElock",), "PELock": (".pelock",),
}
# (name, kind, byte/ASCII markers) -- markers must be specific
STRING_SIGS = (
    ("UPX (banner)", "packer", (b"$Info: This file is packed with the UPX executable packer",)),
    ("PyInstaller bundle", "bundler", (b"MEI\x0c\x0b\x0a\x0b\x0e", b"pyi-runtime-tmpdir", b"PyInstaller:")),
    ("Nuitka (compiled Python)", "bundler", (b"nuitka", b"__nuitka")),
    ("py2exe bundle", "bundler", (b"PYTHONSCRIPT", b"py2exe")),
    ("AutoIt compiled script", "bundler", (b"AU3!EA06", b"AutoIt v3")),
    ("NSIS installer", "installer", (b"Nullsoft Install System", b"NullsoftInst")),
    ("Inno Setup installer", "installer", (b"Inno Setup Setup Data",)),
    ("Go binary", "toolchain", (b"\xff Go buildinf:", b"Go build ID:", b"runtime.gopanic")),
    ("Rust binary", "toolchain", (b"rustc version", b"/rustc/", b"core::panicking")),
    (".NET (mono/CLR metadata)", "toolchain", (b"BSJB", b"mscoree.dll", b"_CorExeMain")),
    ("Delphi / Borland", "toolchain", (b"Borland", b"Embarcadero", b"FastMM")),
    ("Electron / Node bundle", "bundler", (b"electron.asar", b"node_modules")),
    ("Shell script archive (shc / makeself)", "bundler", (b"makeself", b"shc -r")),
)
LOADER_APIS = {"LoadLibraryA", "LoadLibraryW", "LoadLibraryExA", "LoadLibraryExW", "GetProcAddress",
               "VirtualAlloc", "VirtualProtect", "dlopen", "dlsym", "mprotect", "mmap"}


def detect_packers(data: bytes, pb: ParsedBinary | None) -> dict[str, Any]:
    """Return ``{"detections": [...], "indicators": [...], "score": int}``."""
    detections: list[dict[str, Any]] = []
    indicators: list[str] = []

    def add(name: str, kind: str, confidence: str, evidence: str):
        for d in detections:
            if d["name"].split(" ")[0] == name.split(" ")[0] and d["kind"] == kind:
                d["evidence"].append(evidence)
                if confidence == "high":
                    d["confidence"] = "high"
                return
        detections.append({"name": name, "kind": kind, "confidence": confidence, "evidence": [evidence]})

    names = {s.name for s in pb.sections} if pb else set()
    if pb and pb.format == "PE":
        for packer, sigs in PE_SECTION_SIGS.items():
            hit = [n for n in names if n in sigs]
            if hit:
                weak = packer in ("Armadillo",)
                add(packer, "packer", "low" if weak else "medium", f"section name(s): {', '.join(sorted(hit))}")
    if pb and pb.format == "ELF":
        head = data[:0x400]
        if b"UPX!" in head:
            add("UPX", "packer", "high", "UPX! header inside the first 1 KiB of the ELF")
        if pb.protections.get("no_section_headers") and b"UPX!" in data[-0x100:]:
            add("UPX", "packer", "high", "UPX trailer at end of file and no section headers")
    for name, kind, markers in STRING_SIGS:
        hits = [m for m in markers if m in data]
        if hits:
            conf = "high" if (kind == "packer" or len(hits) >= 2) else "medium"
            add(name, kind, conf, "marker: " + ", ".join(repr(h[:40].decode("latin-1")) for h in hits))
    if any(d["name"] == "UPX (banner)" for d in detections) and not any(d["name"] == "UPX" for d in detections):
        for d in detections:
            if d["name"] == "UPX (banner)":
                d["name"] = "UPX"

    if pb:
        hi = [s for s in pb.sections if s.entropy and s.entropy >= 7.2 and s.size >= 1024]
        if hi:
            indicators.append("high-entropy section(s): " + ", ".join(f"{s.name} ({s.entropy:.2f})" for s in hi[:6]))
        ex_hi = [s for s in hi if s.executable]
        if ex_hi:
            indicators.append("executable section with entropy >= 7.2: " + ", ".join(s.name for s in ex_hi))
        if pb.format == "PE":
            imports = {i.get("name") for i in pb.imports if i.get("name")}
            if pb.imports and len(pb.imports) <= 12 and imports & LOADER_APIS:
                indicators.append(f"very small import table ({len(pb.imports)}) containing loader APIs {sorted(imports & LOADER_APIS)}")
            if pb.entry:
                sec = pb.section_for_vaddr(pb.entry)
                if sec is not None and pb.sections and (sec is pb.sections[-1] and len(pb.sections) > 1):
                    indicators.append(f"entry point in the last section ({sec.name})")
            if any(s.size == 0 and s.vsize > 0x4000 and s.executable for s in pb.sections):
                indicators.append("executable section with empty raw data (unpacking stub target)")
            if pb.protections.get("rwx_sections"):
                indicators.append("writable+executable section")
        if pb.format == "ELF":
            if pb.protections.get("no_section_headers"):
                indicators.append("no section headers")
            if pb.protections.get("rwx_segments"):
                indicators.append("writable+executable segment")
            if pb.protections.get("static") and pb.protections.get("stripped") and len(data) < 400_000 and not pb.sections:
                indicators.append("small static binary without section table")
    from .util import entropy as _e
    if (not pb or not pb.sections) and len(data) >= 4096:
        e = _e(data[: 1 << 20])
        if e >= 7.4:
            indicators.append(f"whole-file entropy {e:.2f} with no section structure to explain it")
    score = min(100, 35 * sum(1 for d in detections if d["kind"] in ("packer",) and d["confidence"] != "low")
                + 20 * len(indicators))
    return {"detections": detections, "indicators": indicators, "score": score}
