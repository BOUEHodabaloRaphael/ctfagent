import struct
import subprocess

from fixtures import CRACKME_C, compile_c, strip_binary, need
from rekit.core.diff import diff_files
from rekit.core.formats import parse_binary
from rekit.core.patch import PatchError, PatchOp, apply_patches, invert_branch, nop_bytes, parse_hex
from rekit.core.xrefs import XrefIndex, find_main, find_xrefs


def raises(exc, fn, *a, **kw):
    try:
        fn(*a, **kw)
    except exc:
        return True
    return False


# ---------------------------------------------------------------- branch inversion
def test_invert_x86_short_and_near():
    old, new, d = invert_branch(b"\x74\x05", 0, "x86_64")
    assert (old, new) == (b"\x74", b"\x75") and "je -> jne" in d
    old, new, d = invert_branch(b"\x0f\x84\x10\x00\x00\x00", 0, "x86")
    assert (old, new) == (b"\x0f\x84", b"\x0f\x85")


def test_invert_refuses_non_conditional_bytes():
    assert raises(PatchError, invert_branch, b"\xeb\x05", 0, "x86_64")       # jmp short
    assert raises(PatchError, invert_branch, b"\x90", 0, "x86_64")


def test_invert_arm_aarch64_mips_thumb():
    beq = struct.pack("<I", 0x0A000010)                                      # beq +0x40
    assert invert_branch(beq, 0, "arm")[1] == struct.pack("<I", 0x1A000010)  # bne
    assert raises(PatchError, invert_branch, struct.pack("<I", 0xEA000010), 0, "arm")  # b (always)
    bcond = struct.pack("<I", 0x54000040)                                    # b.eq
    assert invert_branch(bcond, 0, "aarch64")[1] == struct.pack("<I", 0x54000041)  # b.ne
    cbz = struct.pack("<I", 0xB4000040)
    assert invert_branch(cbz, 0, "aarch64")[1] == struct.pack("<I", 0xB5000040)   # cbnz
    beq_mips = struct.pack(">I", 0x10400003)                                 # beq v0, zero
    assert invert_branch(beq_mips, 0, "mips", "big")[1] == struct.pack(">I", 0x14400003)
    assert invert_branch(struct.pack("<H", 0xD005), 0, "arm", mode="thumb")[1] == struct.pack("<H", 0xD105)


def test_nop_encodings():
    assert nop_bytes("x86_64", 3) == b"\x90\x90\x90"
    assert nop_bytes("aarch64", 8) == b"\x1f\x20\x03\xd5" * 2
    assert nop_bytes("arm", 4, mode="thumb") == b"\x00\xbf\x00\xbf"
    assert raises(PatchError, nop_bytes, "arm", 3)


# ---------------------------------------------------------------- applying patches safely
def test_apply_patches_dry_run_expect_inplace_backup(tmp_path):
    f = tmp_path / "t.bin"
    f.write_bytes(b"\x00" * 8 + b"\x74\x05" + b"\x00" * 8)
    assert raises(PatchError, apply_patches, f, [PatchOp(8, b"\x75", expect=b"\xff")])        # wrong expectation
    assert raises(PatchError, apply_patches, f, [PatchOp(100, b"\x75")])                       # outside the file
    r = apply_patches(f, [PatchOp(8, b"\x75", expect=b"\x74")], dry_run=True)
    assert r["output"] is None and f.read_bytes()[8] == 0x74
    r = apply_patches(f, [PatchOp(8, b"\x75", expect=b"\x74")])
    assert (tmp_path / "t.bin.patched").read_bytes()[8] == 0x75 and f.read_bytes()[8] == 0x74   # original untouched
    r = apply_patches(f, [PatchOp(8, b"\x75")], in_place=True)
    assert f.read_bytes()[8] == 0x75 and (tmp_path / "t.bin.bak").read_bytes()[8] == 0x74


def test_parse_hex_variants():
    assert parse_hex("90 90") == parse_hex("0x9090") == parse_hex("90,90") == b"\x90\x90"
    assert raises(PatchError, parse_hex, "zz")


def test_patching_a_crackme_changes_its_behaviour(tmp_path):
    exe = compile_c(tmp_path, CRACKME_C, "crack", ["-no-pie", "-fno-stack-protector"])
    data = exe.read_bytes()
    pb, _ = parse_binary(data)
    # locate `call check; test eax,eax; je` in main and invert the je
    i = data.find(b"\x85\xc0\x74", pb.vaddr_to_offset(pb.symbol_by_name("main").value))
    assert i != -1
    old, new, _ = invert_branch(data, i + 2, pb.arch)
    out = tmp_path / "crack.patched"
    apply_patches(exe, [PatchOp(i + 2, new, expect=old)], out=out)
    ok = subprocess.run([str(out), "wrong"], capture_output=True, text=True)
    good = subprocess.run([str(out), "hunter2"], capture_output=True, text=True)
    assert "Correct password!" in ok.stdout and "Wrong password" in good.stdout
    r = diff_files(data, out.read_bytes())
    assert len(r["byte_ranges"]) == 1 and r["byte_ranges"][0]["length"] == 1 and r["byte_ranges"][0]["section"] == ".text"


# ---------------------------------------------------------------- main discovery and xrefs
def test_find_main_on_stripped_binaries_matches_symbol_truth(tmp_path):
    for name, flags in (("nopie", ["-no-pie"]), ("pie", ["-O2", "-pie", "-fstack-protector-all"])):
        exe = compile_c(tmp_path, CRACKME_C, name, flags)
        truth = parse_binary(exe.read_bytes())[0].symbol_by_name("main").value
        stripped = strip_binary(exe).read_bytes()
        pb, _ = parse_binary(stripped)
        assert pb.symbol_by_name("main") is None
        assert find_main(stripped, pb)["address"] == truth


def test_xref_from_string_to_validation_function_in_stripped_pie(tmp_path):
    exe = compile_c(tmp_path, CRACKME_C, "pie", ["-O2", "-pie"])
    truth = parse_binary(exe.read_bytes())[0].symbol_by_name("main").value
    data = strip_binary(exe).read_bytes()
    pb, _ = parse_binary(data)
    va = pb.offset_to_vaddr(data.find(b"Wrong password"))
    refs = find_xrefs(data, pb, va)
    assert len(refs) == 1 and refs[0]["kind"] == "lea" and refs[0]["function"]["address"] == truth   # one reference, no duplicates


def test_xref_to_function_call(tmp_path):
    exe = compile_c(tmp_path, CRACKME_C, "nopie", ["-no-pie", "-O0"])
    data = exe.read_bytes()
    pb, _ = parse_binary(data)
    refs = find_xrefs(data, pb, pb.symbol_by_name("check").value)
    assert [r["kind"] for r in refs] == ["call"] and refs[0]["function"]["name"] == "main"


def test_xrefs_reject_other_architectures():
    from fixtures import build_macho64
    pb, _ = parse_binary(build_macho64())
    assert raises(ValueError, XrefIndex, build_macho64(), pb)
