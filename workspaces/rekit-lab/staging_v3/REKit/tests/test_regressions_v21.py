"""One regression test per bug listed in the v2.1 test report (legacy/Rapport_REKit_v2.1.pdf)."""
import re
import shutil
import struct
import subprocess
import unittest

from fixtures import CRACKME_C, compile_c, need, strip_binary
from rekit.core.disasm import disassemble
from rekit.core.elf import parse_elf
from rekit.core.formats import parse_binary
from rekit.core.util import entropy

FORTIFY_C = r'''
#include <string.h>
#include <stdio.h>
int main(int argc, char **argv){ char b[16]; if (argc > 1) strcpy(b, argv[1]); else b[0]=0; puts(b); return 0; }
'''


# bug 1 (canary on stripped binaries) -> tests/test_parsers.py::test_elf_canary_detected_on_stripped_binary_regression_v21_bug1
# bug 2 (RC4 alert) -> tests/test_analyzers.py::test_no_rc4_false_positive_on_plain_text
# bug 5/6 (TEA, SHA-1 vs MD5) -> tests/test_analyzers.py::test_tea_* / test_md5_and_sha1_*
# bug 7 (UPX) -> tests/test_analyzers.py::test_upx_requires_structure_not_a_stray_string
# bug 8 (NUL in IOCs) -> tests/test_analyzers.py::test_ioc_registry_and_paths_do_not_contain_nul_bytes_regression_v21


def test_bug3_canary_alone_is_not_reported_as_fortify(tmp_path):
    canary_only = compile_c(tmp_path, CRACKME_C, "canary", ["-fstack-protector-all", "-O0"])
    p = parse_elf(canary_only.read_bytes())
    assert p.protections["canary"] == "yes" and p.protections["fortify"] == "not detected"


def test_bug3_real_fortify_is_still_detected(tmp_path):
    fort = compile_c(tmp_path, FORTIFY_C, "fort", ["-O2", "-D_FORTIFY_SOURCE=2"])
    assert parse_elf(fort.read_bytes()).protections["fortify"] == "yes"


def test_bug4_section_sizes_offsets_and_entropy_match_readelf(tmp_path):
    need("readelf")
    exe = compile_c(tmp_path, CRACKME_C, "plain", [])
    data = exe.read_bytes()
    pb = parse_elf(data)
    out = subprocess.run(["readelf", "-SW", str(exe)], capture_output=True, text=True).stdout
    row = re.compile(r"\]\s+(\S+)\s+\S+\s+([0-9a-f]+)\s+([0-9a-f]+)\s+([0-9a-f]+)\s")
    truth = {m.group(1): (int(m.group(3), 16), int(m.group(4), 16)) for m in row.finditer(out)}   # name -> (offset, size)
    checked = 0
    for s in pb.sections:
        if s.name in truth and s.kind != "NOBITS":
            off, size = truth[s.name]
            assert (s.offset, s.size) == (off, size), s.name
            assert abs(s.entropy - entropy(data[off:off + size])) < 1e-9
            checked += 1
    assert checked >= 10


def elf32_arm_static(big_endian=False):
    """Minimal static ARM ELF with no section headers and no GNU_STACK: the shape of stripped IoT malware."""
    e = ">" if big_endian else "<"
    code = struct.pack(e + "II", 0xE3A00000, 0xE12FFF1E)        # mov r0,#0 ; bx lr
    ehdr = b"\x7fELF" + bytes([1, 2 if big_endian else 1, 1, 0]) + b"\0" * 8
    ehdr += struct.pack(e + "HHIIIIIHHHHHH", 2, 40, 1, 0x8054, 52, 0, 0x5000200, 52, 32, 1, 40, 0, 0)
    ph = struct.pack(e + "IIIIIIII", 1, 0, 0x8000, 0x8000, 0x5C, 0x5C, 5, 0x1000)
    blob = ehdr + ph
    blob += b"\0" * (0x54 - len(blob)) + code
    return blob


def test_bug9_arm_static_stripped_binary_is_parsed_from_machine_type():
    for be in (False, True):
        pb, err = parse_binary(elf32_arm_static(be))
        assert err is None and pb.arch == "arm" and pb.bits == 32 and pb.endian == ("big" if be else "little")
        assert pb.entry == 0x8054 and pb.entry_offset == 0x54
        assert pb.protections["no_section_headers"] and pb.protections["static"] and pb.protections["canary"] == "unknown"
        assert pb.protections["nx"] == "no"                      # no PT_GNU_STACK


def test_bug9_disassembly_starts_at_entry_and_uses_the_header_architecture():
    data = elf32_arm_static()
    pb, _ = parse_binary(data)
    try:
        res = disassemble(data, pb, pb.entry_offset, pb.entry, count=2)
    except RuntimeError as exc:
        raise unittest.SkipTest(f"no ARM-capable disassembler here: {exc}")
    assert res["arch"] == "arm"
    assert [i["mnemonic"] for i in res["instructions"]][:2] == ["mov", "bx"] and res["instructions"][0]["address"] == 0x8054
