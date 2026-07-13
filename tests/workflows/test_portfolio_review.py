from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from smr_app.adapters.contracts import AdapterResult
from smr_app.runtime.migrations import apply_migrations
from smr_app.runtime.runner import WorkflowRunner
from smr_app.workflows.portfolio_review import portfolio_review_definition


class PortfolioReviewWorkflowTests(unittest.TestCase):
    def test_reuses_paper_positions_and_decisions_without_item_growth(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            db_path = root / "runtime.db"
            apply_migrations(db_path)
            conn = sqlite3.connect(db_path)
            conn.executescript(
                """
                CREATE TABLE paper_portfolio_positions (
                    id INTEGER PRIMARY KEY, position_id TEXT, ticker TEXT, market TEXT, quantity REAL,
                    avg_cost REAL, position_pct REAL, status TEXT, opened_at TEXT, closed_at TEXT,
                    source_recommendation_id TEXT, metadata_json TEXT
                );
                CREATE TABLE decision_ledger (
                    decision_id TEXT, ticker TEXT, market TEXT, theme TEXT, action TEXT, status TEXT,
                    decision_time TEXT, thesis_summary TEXT, evidence_ids_json TEXT,
                    bear_case_summary TEXT, kill_conditions_json TEXT, risk_notes TEXT,
                    human_review_status TEXT, outcome_status TEXT, metadata_json TEXT, updated_at TEXT
                );
                """
            )
            conn.executemany(
                "INSERT INTO paper_portfolio_positions VALUES (?, ?, ?, ?, 10, 100, ?, 'open', '2026-07-01', NULL, ?, ?)",
                [
                    (1, "pos-a", "300308.SZ", "A", 24.0, "rec-a", json.dumps({"theme": "AI"})),
                    (2, "pos-b", "0700.HK", "H", 8.0, "rec-b", json.dumps({"theme": "Internet"})),
                ],
            )
            conn.executemany(
                "INSERT INTO decision_ledger VALUES (?, ?, ?, ?, 'hold', 'pending_human_review', '2026-07-12', ?, '[]', '', '[]', '', 'pending', '', '{}', '2026-07-13')",
                [
                    ("dec-a", "300308.SZ", "A", "AI", "thesis a"),
                    ("dec-b", "0700.HK", "H", "Internet", "thesis b"),
                ],
            )
            conn.commit()
            conn.close()

            def scheduler(request):
                return AdapterResult("ok", {"job_id": request.job_id, "dry_run": request.dry_run})

            definition = portfolio_review_definition(artifact_root=root / "artifacts", scheduler=scheduler)
            runner = WorkflowRunner(db_path)
            results = [runner.run(definition, {"allow_network": False}) for _ in range(5)]

            for result in results:
                summary = result["summary"]
                self.assertEqual(summary["position_count"], 2)
                self.assertEqual(summary["decision_count"], 2)
                self.assertEqual(summary["total_exposure_pct"], 32.0)
                self.assertEqual(len(summary["positions"]), 2)
                self.assertEqual(len(summary["artifacts"]), 1)
            self.assertIn("single_position_concentration", results[0]["summary"]["risk_flags"])


if __name__ == "__main__":
    unittest.main()
