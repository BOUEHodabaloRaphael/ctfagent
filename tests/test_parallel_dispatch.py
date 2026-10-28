from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest

_SCRIPT = Path(__file__).resolve().parents[1] / "src" / "tools" / "workspace" / "parallel_dispatch.py"


class ParallelDispatchTest(unittest.TestCase):
    def _make_repo(self, temp_dir: Path) -> Path:
        repo_root = temp_dir
        workspaces = repo_root / "workspaces"
        workspaces.mkdir(parents=True)

        solved = workspaces / "solved-one"
        solved.mkdir()
        (solved / "notes.md").write_text("status: solved\nflag confirmed.\n", encoding="utf-8")

        active = workspaces / "active-one"
        active.mkdir()
        (active / "notes.md").write_text("hypotheses: still probing\n", encoding="utf-8")

        return repo_root

    def test_skips_solved_and_suggests_active(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_root = self._make_repo(Path(temp_dir))

            result = subprocess.run(
                [sys.executable, str(_SCRIPT), "--repo-root", str(repo_root), "--top", "5"],
                capture_output=True,
                text=True,
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["active_workspaces_considered"], 1)
            workspace_names = [s["workspace"] for s in payload["suggestions"]]
            self.assertIn("active-one", workspace_names)
            self.assertNotIn("solved-one", workspace_names)
            self.assertIsNone(payload["applied"])

    def test_missing_workspaces_dir_reports_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = subprocess.run(
                [sys.executable, str(_SCRIPT), "--repo-root", temp_dir],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 1)
            payload = json.loads(result.stdout)
            self.assertFalse(payload["ok"])


if __name__ == "__main__":
    unittest.main()
