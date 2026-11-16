import contextlib
import io
import json
import random

from fixtures import CRACKME_C, build_elf64, build_macho64, build_pe, compile_c, strip_binary
from rekit.cli import main
from rekit.core.reporting import write_html, write_json, write_markdown
from rekit.engine import analyze


def run_cli(*argv):
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = main(list(argv))
    return code, out.getvalue(), err.getvalue()


def sample_dropper(tmp_path):
    p = tmp_path / "dropper.exe"
    p.write_bytes(build_pe(
        {"kernel32.dll": ["VirtualAllocEx", "WriteProcessMemory", "CreateRemoteThread", "LoadLibraryA", "GetProcAddress"], "ws2_32.dll": ["connect", "send", "recv", "socket"]},
        section_names=("UPX0", "UPX1"), rwx_text=True,
        extra_data=b"http://79.124.8.24/fetch.sh\0HKEY_CURRENT_USER\\Software\\Microsoft\\Windows\\CurrentVersion\\Run\\x\0", overlay=b"MZ" * 10))
    return p


# ---------------------------------------------------------------- engine
def test_engine_dropper_report(tmp_path):
    r = analyze(sample_dropper(tmp_path), "malware")
    ids = {f["id"] for f in r["findings"]}
    assert {"MAL-CAP-INJECT", "MAL-PACK-001", "MAL-PE-RWX", "MAL-STR-RUNKEYPERSISTENCE", "MAL-IOC-URLS"} <= ids
    assert r["summary"]["findings_by_severity"]["high"] >= 1 and r["errors"] == []
    assert r["schema_version"] == "2" and r["file"]["format"].startswith("PE 64-bit")
    assert not any(k in json.dumps(r["summary"]).lower() for k in ("malicious", "benign verdict")) or "never emits" in r["summary"]["note"]


def test_engine_ctf_leads_on_stripped_binary(tmp_path):
    exe = strip_binary(compile_c(tmp_path, CRACKME_C, "pie", ["-O2", "-pie"]))
    r = analyze(exe, "ctf")
    lead = next(f for f in r["findings"] if f["id"] == "CTF-LEAD-001")
    assert any("Wrong password" in e for e in lead["evidence"]) and r["errors"] == []
    assert any(s.startswith("rekit disasm") for s in r["summary"]["suggested_next_steps"])


def test_engine_profile_both_does_not_duplicate_iocs(tmp_path):
    r = analyze(sample_dropper(tmp_path), "both")
    ids = [f["id"] for f in r["findings"]]
    assert "MAL-IOC-URLS" in ids and "CTF-IOC-URLS" not in ids and len(ids) == len(set(ids))


def test_engine_handles_garbage_and_empty_files(tmp_path):
    for name, blob in (("empty", b""), ("tiny", b"MZ"), ("junk", bytes(range(256)) * 40), ("badelf", b"\x7fELF" + b"\xff" * 60)):
        p = tmp_path / name
        p.write_bytes(blob)
        r = analyze(p, "both")
        assert r["file"]["size_bytes"] == len(blob)


def test_engine_mutation_fuzz_never_raises(tmp_path):
    rng = random.Random(7)
    seeds = [build_pe({"kernel32.dll": ["VirtualAllocEx", "WriteProcessMemory", "CreateRemoteThread"]}), build_elf64(), build_macho64()]
    for n in range(45):
        b = bytearray(seeds[n % 3])
        for _ in range(rng.randint(1, 10)):
            b[rng.randrange(len(b))] = rng.randrange(256)
        p = tmp_path / f"m{n}.bin"
        p.write_bytes(bytes(b[:rng.randrange(16, len(b))] if rng.random() < 0.3 else b))
        analyze(p, "both")


def test_engine_size_limit(tmp_path):
    p = tmp_path / "big.bin"
    p.write_bytes(b"A" * 2048)
    try:
        analyze(p, "ctf", options={"max_size": 1024})
    except ValueError as exc:
        assert "limit" in str(exc)
    else:
        raise AssertionError("size limit not enforced")


# ---------------------------------------------------------------- reports are safe to open
def hostile_file(tmp_path):
    p = tmp_path / "hostile.bin"
    p.write_bytes(b"password=<script>alert(1)</script>\0secret <img src=x onerror=alert(2)>\0`rm -rf /` token\0http://c2.badhost.xyz/x\0flag{a<b>c}\0| table | break |\0")
    return p


def test_html_report_escapes_everything_and_defangs(tmp_path):
    r = analyze(hostile_file(tmp_path), "both")
    out = tmp_path / "r.html"
    write_html(r, out)
    html = out.read_text()
    assert "<script>alert" not in html and "<img src=x" not in html and "&lt;script&gt;" in html
    assert "http://c2.badhost.xyz" not in html and "hxxp[://]c2[.]badhost[.]xyz" in html
    assert html.count("<script") == 0


def test_markdown_report_neutralises_backticks_and_defangs(tmp_path):
    r = analyze(hostile_file(tmp_path), "both")
    out = tmp_path / "r.md"
    write_markdown(r, out)
    md = out.read_text()
    assert "`rm -rf /`" not in md and "http://c2.badhost.xyz" not in md and "hxxp[://]" in md


def test_json_report_roundtrip_keeps_raw_values(tmp_path):
    r = analyze(hostile_file(tmp_path), "both")
    out = tmp_path / "sub" / "dir" / "r.json"          # directories are created (v3.0 required them to exist)
    write_json(r, out)
    again = json.loads(out.read_text())
    assert again["file"]["sha256"] == r["file"]["sha256"]
    assert "http://c2.badhost.xyz/x" in json.dumps(again)


# ---------------------------------------------------------------- CLI
def test_cli_shorthand_and_formats(tmp_path):
    p = sample_dropper(tmp_path)
    base = tmp_path / "out" / "rep"
    code, out, err = run_cli(str(p), "--format", "json,html,markdown", "--out", str(base))
    assert code == 0 and (tmp_path / "out" / "rep.json").exists() and (tmp_path / "out" / "rep.html").exists() and (tmp_path / "out" / "rep.md").exists()
    code, out, _ = run_cli("analyze", str(p), "--profile", "malware")
    assert "Process injection primitives" in out and "hxxp[://]79[.]124[.]8[.]24" in out
    code, out, _ = run_cli("analyze", str(p), "--no-defang", "--profile", "malware")
    assert "http://79.124.8.24/fetch.sh" in out


def test_cli_strings_hexdump_find_xor_carve(tmp_path):
    exe = compile_c(tmp_path, CRACKME_C, "nopie", ["-no-pie"])
    code, out, _ = run_cli("strings", str(exe), "--grep", "passw")
    assert code == 0 and "Correct password!" in out and ".rodata" in out
    code, out, _ = run_cli("hexdump", str(exe), "--at", "0", "-n", "16")
    assert out.startswith("00400000  7f 45 4c 46")          # shows the virtual address when the offset is mapped
    code, out, _ = run_cli("find", str(exe), "--text", "Wrong password")
    assert code == 0 and "[.rodata]" in out
    code, out, _ = run_cli("find", str(exe), "--hex", "e8 ?? ?? ?? ?? 85 c0", "--max", "2")
    assert code == 0 and out.count("e8") >= 2
    blob = tmp_path / "x.bin"
    blob.write_bytes(b"A" * 64 + bytes(b ^ 0x41 for b in b"https://c2.evil.example/gate.php") + b"Z" * 64)
    code, out, _ = run_cli("xor", str(blob))
    assert code == 0 and "0x41" in out
    emb = tmp_path / "emb.bin"
    emb.write_bytes(b"A" * 100 + build_pe() + b"B" * 10)
    code, out, _ = run_cli("carve", str(emb), "--extract", str(tmp_path / "carved"))
    assert code == 0 and list((tmp_path / "carved").glob("*.exe"))


def test_cli_xrefs_disasm_patch_diff(tmp_path):
    exe = compile_c(tmp_path, CRACKME_C, "nopie", ["-no-pie", "-O0"])
    code, out, _ = run_cli("xrefs", str(exe), "--string", "Wrong password")
    assert code == 0 and "in main" in out
    code, out, _ = run_cli("disasm", str(exe), "--symbol", "main", "-n", "5")
    assert code == 0 and "push" in out
    code, out, _ = run_cli("disasm", str(exe), "--main", "-n", "3")
    assert code == 0 and "engine=" in out
    code, out, err = run_cli("patch", str(exe), "--invert", "0x1", "--dry-run")
    assert code == 2 and "not a conditional jump" in err
    code, out, err = run_cli("patch", str(exe))
    assert code == 2 and "nothing to do" in err
    patched = tmp_path / "p"
    code, out, _ = run_cli("patch", str(exe), "--bytes", "0x1000", "00", "--out", str(patched))
    assert code == 0 and patched.exists()
    code, out, _ = run_cli("diff", str(exe), str(patched))
    assert code == 1 and "DIFFERENT" in out or code == 0


def test_cli_errors_are_clean(tmp_path):
    code, _, err = run_cli("analyze", str(tmp_path / "missing.bin"))
    assert code == 2 and "not found" in err.lower()
    code, _, err = run_cli("unpack", str(tmp_path / "missing.bin"))
    assert code == 2
