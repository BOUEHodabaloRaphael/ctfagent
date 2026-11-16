"""Bridges are tested against stub executables: this validates REKit's invocation and parsing,
NOT the behaviour of the real radare2 / Ghidra (neither is installed in CI)."""
import os
import stat

from fixtures import CRACKME_C
from rekit.cli import main
from rekit.core.integrations import SEP, ToolMissing, ghidra_decompile, r2_summary


def stub(tmp_path, name, body):
    d = tmp_path / "bin"
    d.mkdir(exist_ok=True)
    p = d / name
    p.write_text("#!/bin/sh\n" + body)
    p.chmod(p.stat().st_mode | stat.S_IEXEC)
    return d


def with_path(d, fn):
    old = os.environ["PATH"]
    os.environ["PATH"] = f"{d}:{old}"
    try:
        return fn()
    finally:
        os.environ["PATH"] = old


def test_r2_summary_parses_stub_output(tmp_path):
    body = f'''echo 'noise line'
echo '[{{"name":"main","offset":4198710,"size":80}},{{"name":"sym.imp.puts","offset":4198480,"size":6}}]'
echo '{SEP}'
echo '[{{"vaddr":4202508,"string":"Correct password!"}},{{"vaddr":4202600,"string":"unrelated"}}]'
echo '{SEP}'
echo '  0x00401136 push rbp'
'''
    d = stub(tmp_path, "r2", body)
    res = with_path(d, lambda: r2_summary(tmp_path / "x"))
    assert res["function_count"] == 2 and res["functions"][0]["name"] == "main"
    assert [s["value"] for s in res["interesting_strings"]] == ["Correct password!"] and "push rbp" in res["main_disassembly"][0]


def test_ghidra_bridge_builds_command_and_writes_output(tmp_path):
    body = 'echo "$@" > "$0.args"; echo "INFO noise"; echo "=== main @ 00401136 ==="; echo "int main(void){return 0;}"\n'
    d = stub(tmp_path, "analyzeHeadless", body)
    out = tmp_path / "dec.c"
    res = with_path(d, lambda: ghidra_decompile(tmp_path / "x", out))
    assert res["functions"] == 1 and "int main" in out.read_text() and "INFO" not in out.read_text()
    assert "-deleteProject" in (d / "analyzeHeadless.args").read_text()


def test_missing_tools_are_reported_cleanly(tmp_path):
    old = os.environ["PATH"]
    os.environ["PATH"] = str(tmp_path)
    try:
        for fn in (lambda: r2_summary("x"), lambda: ghidra_decompile("x")):
            try:
                fn()
            except ToolMissing:
                continue
            raise AssertionError("expected ToolMissing")
        assert main(["r2", str(tmp_path / "nofile")]) == 2
    finally:
        os.environ["PATH"] = old
