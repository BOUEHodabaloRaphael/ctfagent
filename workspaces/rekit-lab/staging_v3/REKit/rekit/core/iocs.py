"""Indicator-of-compromise extraction with noise filtering.

Everything is derived from extracted strings, so NUL bytes never leak into matches
(fixes the registry/path pollution found in the v2.1 test report).
"""
from __future__ import annotations

import ipaddress
import re
from typing import Any, Iterable
from urllib.parse import urlsplit

from .fileinfo import extract_strings

URL_RE = re.compile(r"\b(?:https?|ftp)://[^\s\"'<>\x00-\x1f\\^`{|}]{4,}", re.I)
IP_RE = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])")
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,24}\b", re.I)
DOMAIN_RE = re.compile(r"\b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+([a-z]{2,24})\b", re.I)
REGISTRY_RE = re.compile(r"\b(?:HKEY_[A-Z_]+|HK(?:LM|CU|CR|U|CC))\\[^\s\"'<>\x00-\x1f]{3,}", re.I)
WINPATH_RE = re.compile(r"\b[A-Za-z]:\\(?:[^\s\"'<>|?*\x00-\x1f\\]+\\)*[^\s\"'<>|?*\x00-\x1f\\]*")
UNIXPATH_RE = re.compile(r"(?<![\w.:/-])/(?:etc|tmp|var|dev|proc|bin|usr|home|root|opt|sys)/[^\s\"'<>:;|()\x00-\x1f]{1,120}")
UA_RE = re.compile(r"Mozilla/\d\.\d \([^)]{5,150}\)[^\r\n]{0,120}")
BTC_RE = re.compile(r"\b(?:bc1[ac-hj-np-z02-9]{25,60}|[13][a-km-zA-HJ-NP-Z1-9]{25,34})\b")

NOISE_URL_HOSTS = (
    "w3.org", "schemas.microsoft.com", "schemas.openxmlformats.org", "schemas.xmlsoap.org",
    "purl.org", "ns.adobe.com", "www.gnu.org", "gnu.org", "apache.org", "mozilla.org",
    "openssl.org", "example.com", "example.org", "example.net", "xmlsoap.org", "go.microsoft.com",
    "www.verisign.com", "ocsp.", "crl.", "sectigo.com", "digicert.com", "symantec.com",
    "bugs.", "github.com/golang", "golang.org", "python.org", "sun.com", "xmlpull.org",
)
COMMON_TLDS = {
    "com", "net", "org", "info", "biz", "io", "co", "us", "uk", "de", "fr", "ru", "cn", "jp", "br",
    "in", "it", "nl", "es", "pl", "ua", "kr", "ir", "tr", "au", "ca", "ch", "se", "no", "xyz", "top",
    "club", "online", "site", "shop", "store", "tk", "ml", "ga", "cf", "gq", "cc", "tv", "me", "ws",
    "pw", "su", "to", "onion", "link", "live", "app", "dev", "cloud", "tech", "work", "click", "icu",
    "vip", "bid", "win", "download", "stream", "mobi", "name", "pro", "asia", "eu", "africa",
}
FILE_EXT_NOT_TLD = {"so", "dll", "exe", "py", "c", "h", "txt", "conf", "log", "sh", "pl", "rb", "js",
                    "json", "xml", "html", "dat", "bin", "sys", "ini", "cfg", "lib", "a", "o", "ko"}


def classify_ip(ip: str) -> str:
    a = ipaddress.ip_address(ip)
    if a.is_loopback:
        return "loopback"
    if a.is_private:
        return "private"
    if a.is_link_local:
        return "link-local"
    if a.is_multicast:
        return "multicast"
    if a.is_unspecified or a.is_reserved:
        return "reserved"
    return "public"


def _url_is_noise(url: str, host: str) -> bool:
    low = url.lower()
    return any(n in low for n in NOISE_URL_HOSTS) or host.endswith(".local")


def iter_iocs(strings: Iterable[dict[str, Any]]):
    """Yield (type, value, offset, tags) for every candidate indicator."""
    for item in strings:
        s, off = item["value"], item["offset"]
        has_dot, has_colon_slash = "." in s, "://" in s
        if not (has_dot or has_colon_slash or "@" in s or "HK" in s or ":\\" in s or "/" in s or len(s) >= 26):
            continue                                  # nothing in this string can match any indicator regex
        for raw in (URL_RE.findall(s) if has_colon_slash else ()):
            cand = raw.rstrip(".,;:!?)]}'\"")
            try:
                parsed = urlsplit(cand)
                host = parsed.hostname or ""
            except ValueError:
                continue
            if parsed.scheme in ("http", "https", "ftp") and host and ("." in host or host == "localhost"):
                tags = ["noise"] if _url_is_noise(cand, host) else []
                try:
                    if ipaddress.ip_address(host):
                        tags.append("ip-host")
                except ValueError:
                    pass
                yield "url", cand, off, tags
        for raw in (IP_RE.findall(s) if has_dot else ()):
            try:
                ip = str(ipaddress.ip_address(raw))
            except ValueError:
                continue
            if raw != ip:  # leading zeros etc. ("01.02.03.04") are not real addresses
                continue
            kind = classify_ip(ip)
            tags = [kind]
            if kind != "public":
                tags.append("noise")
            if ip in ("8.8.8.8", "8.8.4.4", "1.1.1.1", "9.9.9.9", "208.67.222.222"):
                tags.append("public-dns")
            yield "ip", ip, off, tags
        for raw in (EMAIL_RE.findall(s) if "@" in s else ()):
            yield "email", raw, off, ["noise"] if raw.lower().endswith(("@example.com", "@example.org")) else []
        if "." in s and len(s) < 256 and not s.lower().startswith(("http", "ftp")):
            for m in DOMAIN_RE.finditer(s):
                tld = m.group(1).lower()
                if tld in COMMON_TLDS and tld not in FILE_EXT_NOT_TLD:
                    dom = m.group(0).lower()
                    if not any(n.strip(".") in dom for n in NOISE_URL_HOSTS if not n.endswith(".")) and "@" not in s[max(0, m.start() - 1):m.start()]:
                        yield "domain", dom, off, []
        for raw in (REGISTRY_RE.findall(s) if "\\" in s else ()):
            yield "registry", raw.rstrip(".,;)"), off, []
        for raw in (WINPATH_RE.findall(s) if ":\\" in s else ()):
            if len(raw) > 6:
                yield "windows_path", raw.rstrip(".,;)"), off, []
        for raw in (UNIXPATH_RE.findall(s) if "/" in s else ()):
            yield "unix_path", raw.rstrip(".,;)"), off, []
        for raw in (UA_RE.findall(s) if "Mozilla/" in s else ()):
            yield "user_agent", raw, off, []
        for raw in (BTC_RE.findall(s) if len(s) >= 26 else ()):
            if len(raw) >= 26 and not raw.isalpha():
                yield "crypto_address", raw, off, ["unverified-checksum"]


def extract_iocs_detailed(data: bytes, strings: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    strings = strings if strings is not None else extract_strings(data, min_length=4)
    merged: dict[tuple[str, str], dict[str, Any]] = {}
    for kind, value, off, tags in iter_iocs(strings):
        key = (kind, value)
        if key in merged:
            merged[key]["count"] += 1
        else:
            merged[key] = {"type": kind, "value": value, "offset": off, "tags": tags, "count": 1}
    return sorted(merged.values(), key=lambda x: (x["type"], x["value"]))


PLURAL = {"url": "urls", "ip": "ips", "email": "emails", "domain": "domains", "registry": "registry_keys",
          "windows_path": "windows_paths", "unix_path": "unix_paths", "user_agent": "user_agents",
          "crypto_address": "crypto_addresses"}


def extract_iocs(data: bytes, include_noise: bool = True,
                 strings: list[dict[str, Any]] | None = None) -> dict[str, list[str]]:
    """Return ``{"urls": [...], "ips": [...], "emails": [...], ...}``.

    With ``include_noise=False`` local/private addresses and well-known schema URLs are dropped
    (the analysis profiles do this). The default keeps everything for v3.0 API compatibility.
    The v3.0 keys ``urls``/``ips``/``emails`` are always present.
    """
    out: dict[str, list[str]] = {"urls": [], "ips": [], "emails": []}
    for item in extract_iocs_detailed(data, strings):
        if "noise" in item["tags"] and not include_noise:
            continue
        out.setdefault(PLURAL[item["type"]], []).append(item["value"])
    return {k: sorted(set(v)) for k, v in out.items()}
