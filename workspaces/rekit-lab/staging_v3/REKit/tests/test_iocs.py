from rekit.core.iocs import extract_iocs

def test_iocs_validates_ipv4_and_trims_url():
    data = b"connect https://example.org/path, server 192.168.1.10 invalid 999.1.1.1 user analyst@example.org"
    result = extract_iocs(data)
    assert "https://example.org/path" in result["urls"]
    assert "192.168.1.10" in result["ips"]
    assert "999.1.1.1" not in result["ips"]
    assert "analyst@example.org" in result["emails"]
