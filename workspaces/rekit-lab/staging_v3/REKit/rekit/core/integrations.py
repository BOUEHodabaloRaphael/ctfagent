"""Optional bridges to radare2 and Ghidra (headless).

Both tools are invoked as external processes with a timeout; REKit never links against them.
SECURITY: disassemblers and decompilers parse untrusted input and have had parsing vulnerabilities.
Run these bridges on malware samples only inside an isolated analysis VM/container.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any

SEP = "@@REKIT-SEP@@"
GHIDRA_SCRIPT = '''# @category REKit
from ghidra.app.decompiler import DecompInterface
from ghidra.util.task import ConsoleTaskMonitor
decomp = DecompInterface()
decomp.openProgram(currentProgram)
fm = currentProgram.getFunctionManager()
for func in fm.getFunctions(True):
    if func.isThunk():
        continue
    print("=== " + func.getName() + " @ " + str(func.getEntryPoint()) + " ===")
    res = decomp.decompileFunction(func, 30, ConsoleTaskMonitor())
    if res.decompileCompleted():
        print(res.getDecompiledFunction().getC())
'''
KEYWORDS = ("flag", "ctf", "pass", "key", "secret", "correct", "wrong", "token")


class ToolMissing(RuntimeError):
    pass


def _json_or_none(text: str) -> Any:
    text = text.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def r2_summary(path: str | Path, timeout: int = 180, max_functions: int = 60, disasm_lines: int = 40) -> dict[str, Any]:
    exe = shutil.which("r2") or shutil.which("radare2")
    if not exe:
        raise ToolMissing("radare2 not found in PATH (https://rada.re)")
    script = f"aaa; aflj; ?e {SEP}; izj; ?e {SEP}; pdf @ main"
    proc = subprocess.run([exe, "-2", "-q", "-e", "scr.color=0", "-e", "bin.relocs.apply=true", "-c", script, str(path)],
                          capture_output=True, text=True, timeout=timeout, check=False)
    if proc.returncode != 0 and not proc.stdout:
        raise RuntimeError(f"radare2 failed: {proc.stderr.strip()[:300]}")
    parts = proc.stdout.split(SEP)
    funcs = _json_or_none(parts[0].split("\n", 0)[0] if parts else "") or []
    if not funcs and parts:   # analysis chatter may precede the JSON array
        start = parts[0].find("[")
        funcs = _json_or_none(parts[0][start:]) if start >= 0 else []
        funcs = funcs or []
    strings = _json_or_none(parts[1]) if len(parts) > 1 else []
    strings = strings or []
    disasm = parts[2].strip().splitlines()[:disasm_lines] if len(parts) > 2 else []
    return {
        "function_count": len(funcs),
        "functions": [{"name": f.get("name"), "address": f.get("offset") or f.get("addr"), "size": f.get("size", 0)} for f in funcs[:max_functions]],
        "interesting_strings": [{"address": s.get("vaddr") or s.get("paddr"), "value": s.get("string", "")[:120]}
                                for s in strings if any(k in s.get("string", "").lower() for k in KEYWORDS)][:40],
        "main_disassembly": disasm,
    }


def ghidra_decompile(path: str | Path, out: str | Path | None = None, timeout: int = 600) -> dict[str, Any]:
    exe = shutil.which("analyzeHeadless")
    if not exe:
        raise ToolMissing("analyzeHeadless not found in PATH (install Ghidra and add <ghidra>/support to PATH)")
    with tempfile.TemporaryDirectory(prefix="rekit_ghidra_") as tmp:
        (Path(tmp) / "decompile.py").write_text(GHIDRA_SCRIPT)
        cmd = [exe, tmp, "rekit_proj", "-import", str(path), "-postScript", "decompile.py", "-scriptPath", tmp, "-deleteProject"]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"Ghidra failed (exit {proc.returncode}): {(proc.stderr or proc.stdout).strip()[-300:]}")
    lines = [ln for ln in proc.stdout.splitlines() if not ln.startswith(("INFO", "WARN", "REPORT", "ERROR"))]
    text = "\n".join(lines)
    target = Path(out) if out else Path(str(path) + ".decompiled.c")
    target.write_text(text)
    return {"output": str(target), "functions": text.count("=== "), "bytes": len(text)}
