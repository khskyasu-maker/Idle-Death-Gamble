import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import clean as clean_script  # noqa: E402


class CleanScriptTests(unittest.TestCase):
    def test_clean_script_is_dry_run_by_default_and_removes_known_garbage_only(self):
        original_root = clean_script.ROOT
        try:
            with tempfile.TemporaryDirectory() as tmpdir:
                root = Path(tmpdir)
                clean_script.ROOT = root
                file_targets = [
                    root / ".coverage",
                    root / "results.csv",
                    root / "docs" / "sim-results-old.md",
                ]
                dir_targets = [
                    root / "pachinko-sim" / "__pycache__",
                ]
                keep = root / "docs" / "latest-sim-results.md"
                for path in file_targets:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    path.write_text("garbage", encoding="utf-8")
                for path in dir_targets:
                    path.mkdir(parents=True, exist_ok=True)
                keep.parent.mkdir(parents=True, exist_ok=True)
                keep.write_text("keep", encoding="utf-8")

                with contextlib.redirect_stdout(io.StringIO()):
                    dry_run_targets = clean_script.clean(dry_run=True)
                self.assertTrue(all(path.exists() for path in [*file_targets, *dir_targets]))
                self.assertIn(root / "docs" / "sim-results-old.md", dry_run_targets)

                with contextlib.redirect_stdout(io.StringIO()):
                    clean_script.clean(dry_run=False)
                self.assertTrue(keep.exists())
                self.assertTrue(all(not path.exists() for path in [*file_targets, *dir_targets]))
        finally:
            clean_script.ROOT = original_root


if __name__ == "__main__":
    unittest.main()
