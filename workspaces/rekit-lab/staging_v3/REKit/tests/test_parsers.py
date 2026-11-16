import hashlib
import struct

from fixtures import build_elf64, build_macho64, build_pe, compile_c, CRACKME_C, need, strip_binary
from rekit.core.elf import parse_elf
from rekit.core.formats import parse_binary
from rekit.core.macho import is_fat
from rekit.core.pe import imphash, parse_pe, pe_anomalies, pe_checksum
from rekit.core.patch import fix_pe_checksum


# ---------------------------------------------------------------- ELF
def test_elf_synthetic_imports_and_protections():
    pb = parse_elf(build_elf64(imports=("puts", "gets"), rwx=True, gnu_stack_flags=7))
    assert pb.arch == "x86_64" and pb.bits == 64 and pb.format == "ELF"
    assert [i["name"] for i in pb.imports] == ["puts", "gets"]
    assert pb.protections["nx"] == "no" and pb.protections["rwx_segments"] == 1
    assert pb.sections[0].name == ".text" and pb.entry_offset == 0x1000


def test_elf_big_endian():
    pb = parse_elf(build_elf64(endian=">"))
    assert pb.endian == "big" and [s.name for s in pb.sections][0] == ".text"


def test_elf_real_binary_matches_readelf_protections(tmp_path):
    hard = compile_c(tmp_path, CRACKME_C, "hard", ["-fstack-protector-all", "-O2", "-pie", "-Wl,-z,now,-z,relro"])
    plain = compile_c(tmp_path, CRACKME_C, "plain", ["-no-pie", "-fno-stack-protector", "-Wl,-z,norelro"])
    h, p = parse_elf(hard.read_bytes()), parse_elf(plain.read_bytes())
    assert (h.protections["pie"], h.protections["relro"], h.protections["canary"], h.protections["nx"]) == ("yes", "full", "yes", "yes")
    assert (p.protections["pie"], p.protections["relro"], p.protections["canary"]) == ("no", "no", "not detected")


def test_elf_canary_detected_on_stripped_binary_regression_v21_bug1(tmp_path):
    """v2.1 grepped readelf output for '__stack_chk_fail' and missed versioned names."""
    hard = compile_c(tmp_path, CRACKME_C, "hard", ["-fstack-protector-all", "-pie"])
    stripped = parse_elf(strip_binary(hard).read_bytes())
    assert stripped.protections["canary"] == "yes"
    assert all("@" not in i["name"] for i in stripped.imports)


def test_elf_truncated_and_garbage_do_not_raise():
    good = build_elf64()
    for cut in (4, 20, 52, 64, 100, 0x1000, len(good) - 10):
        parse_binary(good[:cut])  # must return (parsed|None, err) and never raise


# ---------------------------------------------------------------- PE
def test_pe_imports_exports_overlay_and_sections():
    data = build_pe({"kernel32.dll": ["CreateFileA", "VirtualAlloc"], "ws2_32.dll": ["connect"]}, overlay=b"APPENDED" * 8)
    pb = parse_pe(data)
    assert pb.arch == "x86_64" and pb.entry == 0x140001000
    assert [(i["lib"], i["name"]) for i in pb.imports] == [("kernel32.dll", "CreateFileA"), ("kernel32.dll", "VirtualAlloc"), ("ws2_32.dll", "connect")]
    assert pb.overlay == {"offset": len(data) - 64, "size": 64}
    assert pb.protections["aslr"] and pb.protections["dep"]


def test_pe32_parses():
    pb = parse_pe(build_pe(plus=False))
    assert pb.bits == 32 and pb.arch == "x86" and pb.imports[0]["name"] == "ExitProcess"


def test_imphash_algorithm():
    imports = [{"lib": "KERNEL32.dll", "name": "CreateFileA"}, {"lib": "ws2_32.dll", "name": "connect"}]
    assert imphash(imports) == hashlib.md5(b"kernel32.createfilea,ws2_32.connect").hexdigest()


def test_pe_anomalies_flag_rwx_and_odd_names():
    pb = parse_pe(build_pe(rwx_text=True, section_names=("UPX0", "UPX1")))
    ids = {a[0] for a in pe_anomalies(pb, b"")}
    assert {"PE-RWX", "PE-ODD-SECT"} <= ids


def test_pe_checksum_roundtrip():
    buf = bytearray(build_pe())
    new = fix_pe_checksum(buf)
    pb = parse_pe(bytes(buf))
    assert pb.metadata["header_checksum"] == new and pb.metadata["checksum_valid"] is True


def test_pe_with_bad_lfanew_is_rejected_cleanly():
    data = bytearray(build_pe())
    struct.pack_into("<I", data, 0x3C, 0xFFFFFFF0)
    pb, err = parse_binary(bytes(data))
    assert pb is None and err


# ---------------------------------------------------------------- Mach-O
def test_macho_parse():
    pb, err = parse_binary(build_macho64())
    assert err is None and pb.format == "Mach-O" and pb.arch == "aarch64"
    assert pb.metadata["dylibs"] == ["/usr/lib/libSystem.B.dylib"] and pb.protections["pie"] == "yes"
    assert pb.entry == 0x100000F00


def test_fat_header_vs_java_class():
    assert not is_fat(b"\xca\xfe\xba\xbe\x00\x00\x00\x34" + b"\0" * 16)      # Java 1.8 class
    assert is_fat(b"\xca\xfe\xba\xbe\x00\x00\x00\x02" + b"\0" * 40)


# ---------------------------------------------------------------- robustness
def test_mutation_fuzz_never_raises():
    import random
    seeds = [build_pe(), build_elf64(), build_macho64()]
    rng = random.Random(1234)
    for base in seeds:
        for _ in range(250):
            b = bytearray(base)
            for _ in range(rng.randint(1, 12)):
                b[rng.randrange(len(b))] = rng.randrange(256)
            if rng.random() < 0.4:
                b = b[:rng.randrange(8, len(b))]
            parse_binary(bytes(b))
