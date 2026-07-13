from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from smr_app.adapters.memory import create_memory_candidate, get_memory, review_memory
from smr_app.runtime.migrations import apply_migrations
from smr_app.runtime.runner import WorkflowRunner
from smr_app.workflows.thesis_update import thesis_update_definition


class ThesisUpdateWorkflowTests(unittest.TestCase):
    def test_candidate_never_overwrites_approved_and_approval_retains_old_version(self):
        with tempfile.TemporaryDirectory() as directory:
            db_path = Path(directory) / "runtime.db"
            apply_migrations(db_path)
            conn = sqlite3.connect(db_path)
            conn.execute(
                """INSERT INTO memory_items(
                    memory_id, entity_type, entity_id, memory_type, content, status, confidence,
                    version, field_diff_json, created_at, updated_at
                ) VALUES ('memory-v1', 'ticker', '300308.SZ', 'investment_thesis', ?, 'approved', .8, 1, '[]', '2026-07-01', '2026-07-01')""",
                (json.dumps({"thesis": "capacity cycle", "risk": "customer concentration"}),),
            )
            conn.commit()
            candidate = create_memory_candidate(
                conn, entity_type="ticker", entity_id="300308.SZ", memory_type="investment_thesis",
                content={"thesis": "capacity and demand cycle", "risk": "customer concentration"},
                evidence_links=[{"evidence_id": "ev-1", "relation": "supports"}], source_run_id="run-test",
            )
            approved_before = get_memory(conn, "memory-v1")
            self.assertEqual(approved_before["status"], "approved")
            self.assertEqual(approved_before["content"]["thesis"], "capacity cycle")
            self.assertEqual(candidate["status"], "candidate")
            self.assertEqual(candidate["parent_memory_id"], "memory-v1")
            self.assertEqual(candidate["version"], 2)
            self.assertEqual(candidate["field_diff"][0]["field"], "thesis")
            self.assertEqual(candidate["evidence_links"][0]["relation"], "supports")

            reviewed = review_memory(conn, candidate["memory_id"], "approve", "owner", "evidence verified")
            self.assertEqual(reviewed["status"], "approved")
            self.assertEqual(get_memory(conn, "memory-v1")["status"], "archived")
            self.assertEqual(get_memory(conn, "memory-v1")["content"]["thesis"], "capacity cycle")
            conn.close()

    def test_workflow_builds_diff_and_waits_for_review(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db_path = root / "runtime.db"
            apply_migrations(db_path)
            runner = WorkflowRunner(db_path)
            result = runner.run(
                thesis_update_definition(artifact_root=root / "artifacts"),
                {
                    "ticker": "300308.SZ", "allow_network": False,
                    "updates": {"thesis": "demand inflection requires confirmation"},
                    "evidence_links": [{"evidence_id": "ev-2", "relation": "context"}],
                },
            )
            self.assertEqual(result["status"], "waiting_review")
            self.assertTrue(result["summary"]["memory_candidate_id"].startswith("memory_"))
            self.assertEqual(result["summary"]["review_status"], "candidate")
            conn = sqlite3.connect(db_path)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM memory_items").fetchone()[0], 1)
            self.assertEqual(conn.execute("SELECT COUNT(*) FROM workflow_artifacts").fetchone()[0], 1)
            conn.close()


if __name__ == "__main__":
    unittest.main()
