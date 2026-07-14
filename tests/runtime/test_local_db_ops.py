from __future__ import annotations

import sqlite3
import tempfile
import unittest
from contextlib import closing
from pathlib import Path

from scripts.local_db_ops import backup_database, inspect_database, verify_database


class LocalDatabaseOperationsTests(unittest.TestCase):
    def test_online_backup_is_atomic_readable_and_complete(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source.db"
            destination = root / "backups" / "snapshot.db"
            with closing(sqlite3.connect(source)) as conn:
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("CREATE TABLE observations(id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
                conn.executemany(
                    "INSERT INTO observations(value) VALUES (?)",
                    [("first",), ("second",), ("third",)],
                )
                conn.commit()

                result = backup_database(source, destination)

            self.assertEqual("ok", result["integrity_check"])
            self.assertTrue(destination.is_file())
            self.assertFalse(destination.with_name("snapshot.db.partial").exists())
            with closing(sqlite3.connect(destination)) as backup_conn:
                count = backup_conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
            self.assertEqual(3, count)
            self.assertEqual("ok", verify_database(destination)["integrity_check"])

    def test_backup_refuses_to_overwrite_an_existing_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source.db"
            destination = root / "snapshot.db"
            with closing(sqlite3.connect(source)) as conn:
                conn.execute("CREATE TABLE sample(value TEXT)")
            destination.write_bytes(b"keep-me")

            with self.assertRaises(FileExistsError):
                backup_database(source, destination)

            self.assertEqual(b"keep-me", destination.read_bytes())

    def test_inspection_is_read_only_and_reports_missing_migrations(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source.db"
            migrations = root / "migrations"
            migrations.mkdir()
            (migrations / "0000_schema.sql").write_text("CREATE TABLE example(id INTEGER);", encoding="utf-8")
            with closing(sqlite3.connect(source)) as conn:
                conn.execute("CREATE TABLE existing(id INTEGER)")

            before = source.read_bytes()
            inspection = inspect_database(source, migrations)

            self.assertEqual("ok", inspection["quick_check"])
            self.assertEqual(1, inspection["query_only"])
            self.assertEqual(["0000"], inspection["missing_migrations"])
            self.assertEqual(before, source.read_bytes())


if __name__ == "__main__":
    unittest.main()
