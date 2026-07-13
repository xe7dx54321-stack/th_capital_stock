from __future__ import annotations

import sqlite3
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
JOBS = ROOT / "08_scripts" / "jobs"
if str(JOBS) not in sys.path:
    sys.path.insert(0, str(JOBS))

from update_decision_outcomes import record_outcome_prices


class DecisionOutcomeTests(unittest.TestCase):
    def test_price_update_preserves_original_research_judgment(self) -> None:
        conn = sqlite3.connect(":memory:")
        conn.execute(
            """
            CREATE TABLE decision_ledger (
                recommendation_id TEXT PRIMARY KEY,
                thesis_summary TEXT,
                bear_case_summary TEXT,
                kill_conditions_json TEXT,
                outcome_price_1d REAL,
                outcome_price_1w REAL,
                outcome_price_1m REAL,
                outcome_price_3m REAL,
                performance_update_status TEXT,
                performance_update_reason TEXT,
                updated_at TEXT
            )
            """
        )
        conn.execute(
            "INSERT INTO decision_ledger VALUES (?,?,?,?,NULL,NULL,NULL,NULL,NULL,NULL,?)",
            ("rec-1", "原始观点", "原始反方", '["原始失效条件"]', "2026-01-01"),
        )

        record_outcome_prices(
            conn,
            recommendation_id="rec-1",
            prices={"1d": 10.1, "1w": 10.4, "1m": 10.8, "3m": None},
            updated_at="2026-07-13T12:00:00Z",
        )

        row = conn.execute("SELECT * FROM decision_ledger WHERE recommendation_id='rec-1'").fetchone()
        self.assertEqual("原始观点", row[1])
        self.assertEqual("原始反方", row[2])
        self.assertEqual('["原始失效条件"]', row[3])
        self.assertEqual((10.1, 10.4, 10.8, None), row[4:8])
        self.assertEqual("updated", row[8])
        conn.close()


if __name__ == "__main__":
    unittest.main()
