from __future__ import annotations

import sqlite3
import tempfile
import threading
import unittest
from pathlib import Path

from smr_app.runtime.artifact_store import ArtifactPathError, ArtifactStore
from smr_app.runtime.event_store import EventStore
from smr_app.runtime.migrations import apply_migrations


class EventStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.db_path = self.root / "runtime.db"
        apply_migrations(self.db_path)
        conn = sqlite3.connect(self.db_path)
        EventStore(conn).create_run("run_test", "daily_brief", {})
        conn.close()

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_event_sequence_is_monotonic_under_concurrent_writers(self) -> None:
        errors: list[Exception] = []
        barrier = threading.Barrier(12)

        def worker(index: int) -> None:
            try:
                conn = sqlite3.connect(self.db_path, timeout=15)
                barrier.wait()
                EventStore(conn).append_event(
                    "run_test",
                    "stage.progress",
                    f"worker {index}",
                    payload={"worker": index},
                )
                conn.close()
            except Exception as exc:  # pragma: no cover - asserted below
                errors.append(exc)

        threads = [threading.Thread(target=worker, args=(index,)) for index in range(12)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        self.assertEqual([], errors)
        conn = sqlite3.connect(self.db_path)
        events = EventStore(conn).list_events("run_test")
        conn.close()
        self.assertEqual(list(range(1, 13)), [event["sequence"] for event in events])

    def test_after_sequence_returns_only_new_events(self) -> None:
        conn = sqlite3.connect(self.db_path)
        store = EventStore(conn)
        for index in range(3):
            store.append_event("run_test", "stage.progress", str(index))

        events = store.list_events("run_test", after_sequence=1)

        self.assertEqual([2, 3], [event["sequence"] for event in events])
        conn.close()

    def test_artifact_store_rejects_path_traversal(self) -> None:
        artifact_root = self.root / "artifacts"
        artifact_root.mkdir()
        outside = self.root / "secret.txt"
        outside.write_text("secret", encoding="utf-8")
        conn = sqlite3.connect(self.db_path)
        store = ArtifactStore(conn, [artifact_root])

        with self.assertRaises(ArtifactPathError):
            store.register_artifact(
                "run_test",
                "report",
                "Unsafe",
                artifact_root / ".." / "secret.txt",
                "text/plain",
            )
        conn.close()

    def test_artifact_store_persists_relative_path_and_resolves_safely(self) -> None:
        artifact_root = self.root / "artifacts"
        report = artifact_root / "run_test" / "report.md"
        report.parent.mkdir(parents=True)
        report.write_text("# Report", encoding="utf-8")
        conn = sqlite3.connect(self.db_path)
        store = ArtifactStore(conn, [artifact_root])

        artifact = store.register_artifact(
            "run_test", "report", "Research report", report, "text/markdown"
        )

        self.assertEqual("run_test/report.md", artifact["relative_path"])
        self.assertEqual(report.resolve(), store.resolve_artifact(artifact["artifact_id"]))
        conn.close()


if __name__ == "__main__":
    unittest.main()
