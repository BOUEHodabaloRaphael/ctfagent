import hashlib
from rekit.core.fileinfo import detect_type, entropy, extract_strings, inspect_file

def test_detect_elf():
    assert detect_type(b"\x7fELF" + b"\0" * 20) == "ELF"

def test_entropy_empty_and_uniform():
    assert entropy(b"") == 0.0
    assert entropy(b"AAAA") == 0.0
    assert entropy(bytes(range(256))) == 8.0

def test_extract_strings_has_offsets():
    result = extract_strings(b"\x00hello world\x00", min_length=4)
    assert any(x["value"] == "hello world" and x["offset"] == 1 for x in result)

def test_inspect_file(tmp_path):
    p = tmp_path / "sample.bin"
    p.write_bytes(b"MZ" + b"A" * 20)
    _, info = inspect_file(p)
    assert info["type"] == "PE/DOS"
    assert info["sha256"] == hashlib.sha256(p.read_bytes()).hexdigest()
