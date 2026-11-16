from rekit.profiles.ctf import analyze_ctf
from rekit.profiles.malware import analyze_malware_static

def test_ctf_flag_candidate():
    findings, details = analyze_ctf(b"placeholder CTF{hello_world_123} text")
    assert "CTF{hello_world_123}" in details["flag_candidates"]
    assert any(x.id == "CTF-STR-001" for x in findings)

def test_high_entropy_is_low_confidence_not_verdict():
    data = bytes(range(256)) * 8
    findings, _ = analyze_malware_static(data, {"entropy": 8.0, "size_bytes": len(data), "type": "Unknown/raw"}, {"is_elf": False})
    finding = next(x for x in findings if x.id == "MAL-STATIC-ENTROPY")
    assert finding.confidence == "low"
    assert "not proof" in finding.limitations[0].lower()
