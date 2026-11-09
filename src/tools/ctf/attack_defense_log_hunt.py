#!/usr/bin/env python3
"""Zero-dependency helper for the ctf-attack-defense skill's Hunt track.

Implements the cheap "baseline before hypotheses" sweep and the injection-
grammar seed sweep from .claude/skills/ctf-attack-defense/SKILL.md over an
Apache/nginx "combined" access log, without ever reading the whole file into
memory at once in a way that would not scale to a multi-GB log (line-by-line
iteration only).

Usage:
    python3 attack_defense_log_hunt.py baseline access.log
    python3 attack_defense_log_hunt.py injections access.log
"""
from __future__ import annotations

import argparse
import json
import re
import statistics
import urllib.parse
from collections import Counter, defaultdict
from typing import Iterable, Iterator

# Apache/nginx "combined" log format:
# IP - - [timestamp] "METHOD path HTTP/1.1" status size "referer" "user-agent"
COMBINED_LOG_RE = re.compile(
    r'^(?P<ip>\S+) \S+ \S+ \[(?P<timestamp>[^\]]+)\] '
    r'"(?P<method>\S+) (?P<path>\S+) \S+" '
    r'(?P<status>\d{3}) (?P<size>\S+)'
    r'(?: "(?P<referer>[^"]*)" "(?P<user_agent>[^"]*)")?'
)

AUTOMATION_UA_MARKERS = (
    "curl", "python-requests", "sqlmap", "nikto", "wget", "nmap",
    "go-http-client", "scanner", "bot",
)

INJECTION_PATTERNS = {
    "sql_union_select": re.compile(r"union\s+select", re.IGNORECASE),
    "sql_comment": re.compile(r"(--|#|/\*)\s*$"),
    "sql_boolean_pair": re.compile(r"(\bor\b|\band\b)\s+['\"]?1['\"]?\s*=\s*['\"]?1['\"]?", re.IGNORECASE),
    "encoded_quote": re.compile(r"%27|%22"),
    "path_traversal": re.compile(r"\.\./|%2e%2e%2f", re.IGNORECASE),
    "template_injection": re.compile(r"\{\{.*\}\}|\$\{.*\}"),
}

ID_SEGMENT_RE = re.compile(r"^\d+$|^[0-9a-f]{8,}$", re.IGNORECASE)


def iter_log_lines(path: str) -> Iterator[str]:
    """Stream lines from a log file without loading it whole (rule 2: query, don't read)."""
    with open(path, "r", errors="replace") as handle:
        for line in handle:
            yield line.rstrip("\n")


def parse_line(line: str) -> dict | None:
    match = COMBINED_LOG_RE.match(line)
    if not match:
        return None
    row = match.groupdict()
    try:
        row["status"] = int(row["status"])
    except (TypeError, ValueError):
        row["status"] = None
    try:
        row["size"] = int(row["size"])
    except (TypeError, ValueError):
        row["size"] = 0
    return row


def normalize_route(path: str) -> str:
    """Collapse numeric/hex id path segments so /user/123 and /user/456 collapse."""
    query_free = path.split("?", 1)[0]
    segments = [
        "{id}" if ID_SEGMENT_RE.match(seg) else seg
        for seg in query_free.split("/")
    ]
    return "/".join(segments) or "/"


def is_automation_ua(user_agent: str | None) -> bool:
    if not user_agent:
        return True  # empty UA is itself a signal
    lowered = user_agent.lower()
    return any(marker in lowered for marker in AUTOMATION_UA_MARKERS)


def status_histogram(rows: Iterable[dict]) -> Counter:
    return Counter(row["status"] for row in rows if row.get("status") is not None)


def top_talkers(rows: Iterable[dict], n: int = 10) -> list[tuple[str, int]]:
    return Counter(row["ip"] for row in rows if row.get("ip")).most_common(n)


def top_routes(rows: Iterable[dict], n: int = 10) -> list[tuple[str, int]]:
    return Counter(normalize_route(row["path"]) for row in rows if row.get("path")).most_common(n)


def user_agent_inventory(rows: Iterable[dict]) -> dict:
    uas = [row.get("user_agent") for row in rows]
    counted = Counter(uas)
    flagged = {ua: count for ua, count in counted.items() if is_automation_ua(ua)}
    return {"all": counted.most_common(10), "flagged_automation": flagged}


def response_size_outliers(rows: Iterable[dict], z_threshold: float = 3.5) -> dict:
    """Per normalized route, flag requests whose size is far from that route's
    median using a modified (MAD-based) z-score, which stays robust even when
    the outlier itself is part of the small sample (a plain stdev z-score is
    not: a single huge outlier inflates stdev enough to mask itself)."""
    by_route: dict[str, list[int]] = defaultdict(list)
    for row in rows:
        if row.get("path") is None:
            continue
        by_route[normalize_route(row["path"])].append(row.get("size", 0))

    outliers: dict[str, dict] = {}
    for route, sizes in by_route.items():
        if len(sizes) < 5:
            continue
        median = statistics.median(sizes)
        abs_deviations = [abs(s - median) for s in sizes]
        mad = statistics.median(abs_deviations)
        if mad == 0:
            continue
        outlier_sizes = [
            s for s in sizes
            if 0.6745 * abs(s - median) / mad > z_threshold
        ]
        if outlier_sizes:
            outliers[route] = {
                "median": median,
                "mad": round(mad, 1),
                "sample_count": len(sizes),
                "outlier_sizes": outlier_sizes[:10],
            }
    return outliers


def detect_injection_grammar(rows: Iterable[dict]) -> list[dict]:
    """Seed sweep #4: injection grammar in query strings/paths.

    URL-decodes the path first (once) since attack payloads are almost
    always percent-encoded in the raw log line (%27, %20, ...) and the
    grammar patterns below are written against the decoded form.
    """
    hits = []
    for row in rows:
        raw_path = row.get("path") or ""
        decoded_path = urllib.parse.unquote(raw_path)
        combined = raw_path + " " + decoded_path
        for name, pattern in INJECTION_PATTERNS.items():
            if pattern.search(combined):
                hits.append({
                    "ip": row.get("ip"),
                    "path": raw_path,
                    "pattern": name,
                    "status": row.get("status"),
                })
    return hits


def baseline_sweep(path: str) -> dict:
    rows = [r for r in (parse_line(line) for line in iter_log_lines(path)) if r is not None]
    return {
        "total_requests": len(rows),
        "status_histogram": dict(status_histogram(rows)),
        "top_talkers": top_talkers(rows),
        "top_routes": top_routes(rows),
        "user_agents": user_agent_inventory(rows),
        "response_size_outliers": response_size_outliers(rows),
    }


def injections_sweep(path: str) -> list[dict]:
    rows = [r for r in (parse_line(line) for line in iter_log_lines(path)) if r is not None]
    return detect_injection_grammar(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["baseline", "injections"])
    parser.add_argument("logfile")
    args = parser.parse_args()

    if args.mode == "baseline":
        print(json.dumps(baseline_sweep(args.logfile), indent=2, default=str))
    else:
        print(json.dumps(injections_sweep(args.logfile), indent=2, default=str))


if __name__ == "__main__":
    main()
