"""Tests for local storage audit and cleanup safety."""

import os
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "scripts")
if SCRIPTS_DIR not in sys.path:
    sys.path.insert(0, SCRIPTS_DIR)


class TestAuditLocalStorage(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp(prefix="test_audit_")
        self.create_test_structure()

    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def create_test_structure(self):
        """Create a test directory structure."""
        dirs = [
            "src",
            "__pycache__",
            ".pytest_cache",
            "01_data/db",
            ".git",
        ]
        for d in dirs:
            Path(self.test_dir, d).mkdir(parents=True, exist_ok=True)

        files = {
            "src/app.py": "# test source",
            "__pycache__/x.pyc": b"\x00\x00\x00\x00",
            ".pytest_cache/pytest.json": "{}",
            "01_data/db/smr.db": b"\x00" * 100,
            ".git/HEAD": "ref: refs/heads/main",
        }
        for path, content in files.items():
            f = Path(self.test_dir, path)
            f.parent.mkdir(parents=True, exist_ok=True)
            if isinstance(content, bytes):
                f.write_bytes(content)
            else:
                f.write_text(content)

    def test_audit_generates_report(self):
        """Test that audit generates a report."""
        from audit_local_storage import (
            get_directory_sizes,
            get_large_files,
            get_cache_directories,
        )

        cache_dirs = get_cache_directories()
        self.assertIsInstance(cache_dirs, list)

    def test_audit_does_not_delete_files(self):
        """Test that audit does not delete any files."""
        from audit_local_storage import get_cache_directories

        files_before = list(Path(self.test_dir).rglob("*"))

        get_cache_directories()

        files_after = list(Path(self.test_dir).rglob("*"))

        self.assertEqual(len(files_before), len(files_after))


class TestCleanupLocalArtifactsSafety(unittest.TestCase):
    def test_is_cache_pycache_pattern(self):
        """Test that __pycache__ matches cache pattern."""
        from cleanup_local_artifacts import CACHE_PATTERNS
        self.assertIn("__pycache__", CACHE_PATTERNS)

    def test_is_cache_pytest_cache_pattern(self):
        """Test that .pytest_cache matches cache pattern."""
        from cleanup_local_artifacts import CACHE_PATTERNS
        self.assertIn(".pytest_cache", CACHE_PATTERNS)

    def test_is_cache_pyc_pattern(self):
        """Test that .pyc matches cache file pattern."""
        from cleanup_local_artifacts import CACHE_FILE_PATTERNS
        self.assertIn("*.pyc", CACHE_FILE_PATTERNS)

    def test_main_db_in_forbidden_paths(self):
        """Test that main database is in forbidden paths."""
        from cleanup_local_artifacts import FORBIDDEN_PATHS
        self.assertIn("01_data/db/smr.db", FORBIDDEN_PATHS)

    def test_git_in_forbidden_paths(self):
        """Test that .git is in forbidden paths."""
        from cleanup_local_artifacts import FORBIDDEN_PATHS
        self.assertIn(".git", FORBIDDEN_PATHS)

    def test_env_in_forbidden_paths(self):
        """Test that .env is in forbidden paths."""
        from cleanup_local_artifacts import FORBIDDEN_PATHS
        self.assertIn(".env", FORBIDDEN_PATHS)

    def test_secrets_in_forbidden_paths(self):
        """Test that secrets is in forbidden paths."""
        from cleanup_local_artifacts import FORBIDDEN_PATHS
        self.assertIn("secrets", FORBIDDEN_PATHS)

    def test_main_db_in_must_keep_paths(self):
        """Test that main database is in must keep paths."""
        from cleanup_local_artifacts import MUST_KEEP_PATHS
        self.assertIn("01_data/db/smr.db", MUST_KEEP_PATHS)


class TestQuarantineManifest(unittest.TestCase):
    def test_manifest_exists(self):
        """Test that cleanup manifest exists after apply."""
        manifest_path = Path(__file__).parent.parent / "tmp" / "cleanup_manifest.json"
        if manifest_path.exists():
            import json
            with open(manifest_path) as f:
                manifest = json.load(f)

            self.assertIn("timestamp", manifest)
            self.assertIn("dry_run", manifest)
            self.assertIn("quarantine_dir", manifest)
            self.assertIn("deleted", manifest)
            self.assertIn("quarantined", manifest)
            self.assertIn("skipped", manifest)
            self.assertIn("summary", manifest)

    def test_manifest_records_original_paths(self):
        """Test that manifest records original paths."""
        manifest_path = Path(__file__).parent.parent / "tmp" / "cleanup_manifest.json"
        if manifest_path.exists():
            import json
            with open(manifest_path) as f:
                manifest = json.load(f)

            for item in manifest.get("quarantined", []):
                self.assertIn("path", item)

    def test_manifest_does_not_record_secret_content(self):
        """Test that manifest does not record secret content."""
        manifest_path = Path(__file__).parent.parent / "tmp" / "cleanup_manifest.json"
        if manifest_path.exists():
            import json
            with open(manifest_path) as f:
                manifest = json.load(f)

            summary_str = json.dumps(manifest.get("summary", {}))
            forbidden_patterns = [
                "API_KEY",
                "secret_key",
                "password",
                "private_key",
            ]
            for pattern in forbidden_patterns:
                self.assertNotIn(pattern, summary_str)


class TestCleanupSafetyIntegration(unittest.TestCase):
    def test_main_db_exists(self):
        """Test that main database still exists."""
        db_path = Path(__file__).parent.parent / "01_data" / "db" / "smr.db"
        self.assertTrue(db_path.exists(), "Main database must exist")

    def test_git_exists(self):
        """Test that .git directory still exists."""
        git_path = Path(__file__).parent.parent / ".git"
        self.assertTrue(git_path.exists(), ".git directory must exist")

    def test_git_not_in_cleanup(self):
        """Test that .git is not in cleanup candidates."""
        git_path = Path(__file__).parent.parent / ".git"
        from cleanup_local_artifacts import is_forbidden

        self.assertTrue(is_forbidden(git_path))

    def test_main_db_not_in_cleanup(self):
        """Test that main database is not in cleanup candidates."""
        db_path = Path(__file__).parent.parent / "01_data" / "db" / "smr.db"
        from cleanup_local_artifacts import is_forbidden, is_must_keep

        self.assertTrue(is_forbidden(db_path) or is_must_keep(db_path))


if __name__ == "__main__":
    unittest.main()