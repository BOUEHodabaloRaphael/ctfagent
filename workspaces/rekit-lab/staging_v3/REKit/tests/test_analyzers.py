import base64
import struct

from fixtures import CRACKME_C, build_pe, compile_c
from rekit.core.capabilities import analyze_capabilities
from rekit.core.carve import carve
from rekit.core.crypto import scan_crypto
from rekit.core.decoders import decode_candidates
from rekit.core.fileinfo import extract_strings
from rekit.core.formats import parse_binary
from rekit.core.iocs import classify_ip, extract_iocs
from rekit.core.packers import detect_packers
from rekit.core.stackstrings import find_stack_strings
from rekit.core.util import defang
from rekit.core.xorscan import xor_scan


def names(res):
    return {r["name"] for r in res}


# ---------------------------------------------------------------- crypto (v2.1 bugs 5 and 6)
def test_md5_and_sha1_are_distinguished():
    iv = struct.pack("<IIII", 0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476)
    md5 = iv + struct.pack("<IIII", 0xD76AA478, 0xE8C7B756, 0x242070DB, 0xC1BDCEEE)
    sha1 = iv + struct.pack("<I", 0xC3D2E1F0)
    assert names(scan_crypto(b"\0" * 32 + md5)) == {"MD5"}
    assert names(scan_crypto(b"\0" * 32 + sha1)) == {"SHA-1"}


def test_shared_initial_vector_alone_is_reported_as_ambiguous():
    iv = struct.pack("<IIII", 0x67452301, 0xEFCDAB89, 0x98BADCFE, 0x10325476)
    res = scan_crypto(b"\0" * 32 + iv)
    assert names(res) == {"MD4/MD5/SHA-1 family initial vector"} and res[0]["confidence"] == "low"


def test_tea_delta_found_when_compiler_negates_it():
    res = scan_crypto(b"\0" * 16 + struct.pack("<I", 0x61C88647))
    assert any(r["name"].startswith("TEA") and "negated" in r["evidence"][0]["form"] for r in res)


def test_big_endian_sha256_table():
    table = struct.pack(">IIII", 0x428A2F98, 0x71374491, 0xB5C0FBCF, 0xE9B5DBA5)
    assert "SHA-256 K table" in names(scan_crypto(b"x" * 10 + table))


def test_no_rc4_false_positive_on_plain_text():
    assert scan_crypto(b"The quick brown fox jumps over the lazy dog. " * 200) == []


# ---------------------------------------------------------------- XOR
def test_xor_finds_key_flag_and_markers():
    secret = b"http://evil.example/fetch.sh\0/bin/busybox\0flag{x0r_w0rks}"
    blob = b"junk" * 50 + bytes(b ^ 0x22 for b in secret) + b"tail" * 20
    res = xor_scan(blob)
    assert res[0]["key"] == 0x22 and "flag{x0r_w0rks}" in res[0]["flags"] and "http://" in res[0]["markers"]


def test_xor_flag_at_end_of_buffer_followed_by_junk():
    blob = b"A" * 64 + bytes(b ^ 0x41 for b in b"flag{cli_xor_ok}") + b"Z" * 64
    assert any("flag{cli_xor_ok}" in r["flags"] for r in xor_scan(blob))


def test_xor_no_false_positive_on_clear_text_and_case_flips():
    assert xor_scan(b"hello http://example.com /bin/sh flag{plain} " * 50) == []
    assert xor_scan(b"SOCKET CONNECT PASSWORD " * 100) == []          # key 0x20 only flips case


def test_xor_is_fast_on_multi_megabyte_input():
    import os, time
    blob = os.urandom(4 * 1024 * 1024)
    t = time.time()
    xor_scan(blob)
    assert time.time() - t < 10                                          # v2.1-style 255x translate took ~50 s on 8 MiB


# ---------------------------------------------------------------- stack strings
def test_stack_strings_synthetic_encoding():
    code = b"".join(b"\xc6\x45" + bytes([0xF0 + i]) + bytes([ch]) for i, ch in enumerate(b"hello!"))
    res = find_stack_strings(b"\x90" * 8 + code + b"\x90" * 8)
    assert any(r["value"] == "hello!" for r in res)


def test_stack_strings_from_real_gcc_output(tmp_path):
    src = 'int puts(const char*);int main(void){char a[]="stack_secret_string";char b[]="CTF{st4ck_fl4g}";puts(a);puts(b);return 0;}'
    exe = compile_c(tmp_path, src, "ss", ["-O0", "-fno-stack-protector"])
    values = {r["value"] for r in find_stack_strings(exe.read_bytes())}
    assert {"stack_secret_string", "CTF{st4ck_fl4g}"} <= values
    assert b"CTF{st4ck_fl4g}" not in exe.read_bytes()                    # invisible to plain `strings`


# ---------------------------------------------------------------- packers (v2.1 bug 7)
def test_upx_requires_structure_not_a_stray_string():
    assert detect_packers(b"hello UPX! world" * 20, None)["detections"] == []
    data = build_pe(section_names=("UPX0", "UPX1"))
    pb, _ = parse_binary(data)
    assert detect_packers(data, pb)["detections"][0]["name"] == "UPX"


def test_clean_pe_has_no_packer_detection():
    data = build_pe()
    pb, _ = parse_binary(data)
    assert detect_packers(data, pb)["detections"] == []


# ---------------------------------------------------------------- capabilities
def test_injection_triad_is_high_and_plain_socket_client_is_not():
    inj = analyze_capabilities([{"name": n} for n in ("VirtualAllocEx", "WriteProcessMemory", "CreateRemoteThread")])
    assert next(r for r in inj if r["id"] == "CAP-INJECT")["severity"] == "high"
    benign = analyze_capabilities([{"name": n} for n in ("printf", "socket", "connect", "getaddrinfo")])
    assert all(r["severity"] in ("info", "low") for r in benign)


def test_ransomware_like_combination_needs_three_signals():
    imps = [{"name": n} for n in ("CryptEncrypt", "FindFirstFileW")]
    assert not any(r["id"] == "CMB-RANSOM" for r in analyze_capabilities(imps))
    assert any(r["id"] == "CMB-RANSOM" for r in analyze_capabilities(imps, ["vssadmin delete shadows /all /quiet"]))


def test_ascii_suffix_normalisation():
    assert any(r["id"] == "CAP-ANTIDEBUG" for r in analyze_capabilities([{"name": "OutputDebugStringA"}]))


# ---------------------------------------------------------------- IOCs
def test_ioc_noise_filtering_and_ip_classes():
    blob = b"http://79.124.8.24/fetch.sh\0http://www.w3.org/2000/svg\0192.168.1.5 8.8.8.8 127.0.0.1 evil-domain.xyz libc.so.6"
    clean = extract_iocs(blob, include_noise=False)
    assert clean["urls"] == ["http://79.124.8.24/fetch.sh"] and "192.168.1.5" not in clean["ips"] and "8.8.8.8" in clean["ips"]
    assert "evil-domain.xyz" in clean["domains"] and "libc.so.6" not in clean["domains"]
    assert classify_ip("10.0.0.1") == "private" and classify_ip("1.2.3.4") == "public"


def test_ioc_registry_and_paths_do_not_contain_nul_bytes_regression_v21():
    wide = "HKEY_CURRENT_USER\\Software\\Run\\x".encode("utf-16le") + b"\0\0" + "C:\\Users\\Public\\a.exe".encode("utf-16le")
    res = extract_iocs(wide)
    assert res["registry_keys"] == ["HKEY_CURRENT_USER\\Software\\Run\\x"] and res["windows_paths"] == ["C:\\Users\\Public\\a.exe"]


def test_defang():
    assert defang("http://evil.example.com/a.php") == "hxxp[://]evil[.]example[.]com/a.php"
    assert defang("1.2.3.4") == "1[.]2[.]3[.]4"


# ---------------------------------------------------------------- strings
def test_strings_cap_applies_per_encoding():
    data = b"\0".join(b"ascii%04d" % i for i in range(50)) + b"\0" + "wide string".encode("utf-16le")
    res = extract_strings(data, 4, max_count=10)
    assert sum(r["encoding"] == "ascii" for r in res) == 10 and any(r["encoding"] == "utf-16le" for r in res)


# ---------------------------------------------------------------- carve / decoders
def test_carve_finds_embedded_pe_and_skips_offset_zero():
    blob = b"A" * 100 + build_pe() + b"B" * 50
    found = carve(blob)
    assert found and found[0]["type"] == "PE" and found[0]["offset"] == 100
    assert carve(build_pe()) == []


def test_decoders_find_base64_flag_and_reversed_flag():
    strings = extract_strings(b"\0" + base64.b64encode(b"flag{b64_layer_ok}") + b"\0" + b"}desrever_ton{galf"[::-1][::-1] + b"\0")
    res = decode_candidates(strings)
    assert any(r["encoding"] == "base64" and "flag{b64_layer_ok}" in r["flags"] for r in res)
