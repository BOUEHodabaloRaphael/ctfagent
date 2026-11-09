from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "tools"
    / "ctf"
    / "attack_defense_log_hunt.py"
)
SPEC = importlib.util.spec_from_file_location("attack_defense_log_hunt", SCRIPT_PATH)
log_hunt = importlib.util.module_from_spec(SPEC)
assert SPEC is not None
assert SPEC.loader is not None
SPEC.loader.exec_module(log_hunt)


# Minimal synthetic "combined" access log fixture: a benign baseline plus
# one SQLi-shaped request and one oversized response on an otherwise small
# route, matching the Hunt track's seed sweeps #4 (injection grammar) and
# #7 (size anomalies) in .claude/skills/ctf-attack-defense/SKILL.md.
SAMPLE_LOG_LINES = [
    '10.0.0.1 - - [09/Nov/2026:10:00:00 +0000] "GET /user/1 HTTP/1.1" 200 180 "-" "Mozilla/5.0"',
    '10.0.0.1 - - [09/Nov/2026:10:00:01 +0000] "GET /user/2 HTTP/1.1" 200 182 "-" "Mozilla/5.0"',
    '10.0.0.1 - - [09/Nov/2026:10:00:02 +0000] "GET /user/3 HTTP/1.1" 200 179 "-" "Mozilla/5.0"',
    '10.0.0.1 - - [09/Nov/2026:10:00:03 +0000] "GET /user/4 HTTP/1.1" 200 181 "-" "Mozilla/5.0"',
    '10.0.0.1 - - [09/Nov/2026:10:00:04 +0000] "GET /user/5 HTTP/1.1" 200 183 "-" "Mozilla/5.0"',
    '203.0.113.9 - - [09/Nov/2026:10:05:00 +0000] "GET /user/6?id=1%27%20OR%20%271%27=%271 HTTP/1.1" 200 4096 "-" "python-requests/2.31"',
]


class AttackDefenseLogHuntTest(unittest.TestCase):
    def _write_log(self) -> str:
        handle = tempfile.NamedTemporaryFile(mode="w", suffix=".log", delete=False)
        handle.write("\n".join(SAMPLE_LOG_LINES) + "\n")
        handle.close()
        return handle.name

    def test_normalize_route_collapses_numeric_ids(self) -> None:
        self.assertEqual(log_hunt.normalize_route("/user/123"), "/user/{id}")
        self.assertEqual(log_hunt.normalize_route("/user/123?x=1"), "/user/{id}")
        self.assertEqual(log_hunt.normalize_route("/login"), "/login")

    def test_is_automation_ua_flags_known_tools_and_empty(self) -> None:
        self.assertTrue(log_hunt.is_automation_ua("python-requests/2.31"))
        self.assertTrue(log_hunt.is_automation_ua(""))
        self.assertTrue(log_hunt.is_automation_ua(None))
        self.assertFalse(log_hunt.is_automation_ua("Mozilla/5.0 (Windows NT 10.0)"))

    def test_baseline_sweep_detects_automation_ua_and_outlier(self) -> None:
        path = self._write_log()
        result = log_hunt.baseline_sweep(path)
        self.assertEqual(result["total_requests"], 6)
        self.assertIn(200, result["status_histogram"])
        flagged = result["user_agents"]["flagged_automation"]
        self.assertTrue(any("python-requests" in ua for ua in flagged))
        self.assertIn("/user/{id}", result["response_size_outliers"])

    def test_injections_sweep_flags_sqli_shaped_request(self) -> None:
        path = self._write_log()
        hits = log_hunt.injections_sweep(path)
        self.assertTrue(hits, "expected at least one injection-grammar hit")
        patterns_found = {hit["pattern"] for hit in hits}
        self.assertIn("sql_boolean_pair", patterns_found)
        self.assertIn("encoded_quote", patterns_found)
        self.assertEqual(hits[0]["ip"], "203.0.113.9")

    def test_injections_sweep_is_quiet_on_benign_traffic(self) -> None:
        path = self._write_log()
        rows = [r for r in (log_hunt.parse_line(l) for l in SAMPLE_LOG_LINES[:5]) if r]
        hits = log_hunt.detect_injection_grammar(rows)
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
