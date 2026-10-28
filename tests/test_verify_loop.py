from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

_SCRIPT = Path(__file__).resolve().parents[1] / "src" / "tools" / "workspace" / "verify_loop.py"


class VerifyLoopTest(unittest.TestCase):
    def test_finds_flag_from_discovered_script(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            workspace = repo_root / "workspaces" / "demo"
            workspace.mkdir(parents=True)
            (workspace / "exp_flag.py").write_text(
                "print('connecting...')\nprint('FLAG{demo_ok_123}')\n", encoding="utf-8"
            )

            result = subprocess.run(
                [
                    sys.executable,
                    str(_SCRIPT),
                    "--workspace",
                    str(workspace),
                    "--repo-root",
                    str(repo_root),
                ],
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            summary = json.loads(result.stdout)
            self.assertTrue(summary["ok"])
            self.assertEqual(summary["flag"], "FLAG{demo_ok_123}")
            self.assertTrue((workspace / "verify_log.jsonl").exists())
            self.assertTrue(Path(summary["pending_flag_file"]).exists())
            self.assertEqual(
                Path(summary["pending_flag_file"]).read_text(encoding="utf-8"), "FLAG{demo_ok_123}"
            )

    def test_no_candidate_script_is_reported_as_failure(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            workspace = repo_root / "workspaces" / "empty"
            workspace.mkdir(parents=True)

            result = subprocess.run(
                [sys.executable, str(_SCRIPT), "--workspace", str(workspace), "--repo-root", str(repo_root)],
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 1)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["ok"])

    def test_explicit_cmd_without_flag_leaves_no_pending_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = Path(temp_dir)
            workspace = repo_root / "workspaces" / "demo2"
            workspace.mkdir(parents=True)
            (workspace / "try.py").write_text("print('no luck here')\n", encoding="utf-8")

            result = subprocess.run(
                [
                    sys.executable,
                    str(_SCRIPT),
                    "--workspace",
                    str(workspace),
                    "--repo-root",
                    str(repo_root),
                    "--cmd",
                    f"{sys.executable} try.py",
                ],
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 1)
            summary = json.loads(result.stdout)
            self.assertFalse(summary["ok"])
            self.assertIsNone(summary["flag"])
            self.assertFalse((repo_root / "flags" / "pending").exists())


if __name__ == "__main__":
    unittest.main()
