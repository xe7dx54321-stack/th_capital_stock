from __future__ import annotations

import sqlite3
import tempfile
import unittest
from pathlib import Path

from smr_app.runtime.migrations import MigrationChecksumError, apply_migrations


class MigrationTests(unittest.TestCase):
    def test_default_migrations_are_ordered_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "runtime.db"

            first = apply_migrations(db_path)
            second = apply_migrations(db_path)

            self.assertEqual(["0000", "0001", "0002"], first.applied_versions)
            self.assertEqual([], second.applied_versions)
            conn = sqlite3.connect(db_path)
            try:
                versions = [row[0] for row in conn.execute("SELECT version FROM schema_migrations ORDER BY version")]
                self.assertEqual(["0000", "0001", "0002"], versions)
                self.assertEqual("ok", conn.execute("PRAGMA integrity_check").fetchone()[0])
            finally:
                conn.close()

    def test_existing_risk_columns_are_skipped_safely(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "runtime.db"
            conn = sqlite3.connect(db_path)
            conn.executescript(
                """
                CREATE TABLE risk_alert (
                    alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_time TEXT NOT NULL,
                    alert_type TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    fingerprint TEXT
                );
                """
            )
            conn.close()

            result = apply_migrations(db_path)

            self.assertEqual(["0000", "0001", "0002"], result.applied_versions)

    def test_changed_applied_migration_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            migration_dir = root / "migrations"
            migration_dir.mkdir()
            migration = migration_dir / "0000_bootstrap.sql"
            migration.write_text("CREATE TABLE sample (id INTEGER PRIMARY KEY);", encoding="utf-8")
            db_path = root / "runtime.db"
            apply_migrations(db_path, migration_dir)
            migration.write_text("CREATE TABLE sample (id TEXT PRIMARY KEY);", encoding="utf-8")

            with self.assertRaises(MigrationChecksumError):
                apply_migrations(db_path, migration_dir)


if __name__ == "__main__":
    unittest.main()
