import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
if str(REPORTING_DIR) not in sys.path:
    sys.path.insert(0, str(REPORTING_DIR))

from build_phase8_blocker_triage import aggregate_blockers, upsert_queue_from_triage
from smr_blocker_taxonomy import normalize_blocker
from smr_live_run_history import record_live_run_history
from smr_blocker_repair_queue import list_repair_tasks


class Phase8BlockerTriageTests(unittest.TestCase):
    def test_normalizes_legacy_blocker_codes(self):
        blocker = normalize_blocker(
            {"code": "fundamentals_snapshot_fresh_or_explainable", "severity": "blocker"},
            context={"fundamentals_missing_fields": ["gross_profit"]},
        )

        self.assertEqual(blocker["code"], "FUNDAMENTALS_MISSING_FIELDS")
        self.assertEqual(blocker["type"], "fundamentals")
        self.assertEqual(blocker["affected_fields"], ["gross_profit"])

    def test_aggregates_repeated_blockers_and_upserts_queue(self):
        conn = sqlite3.connect(":memory:")
        record_live_run_history(
            conn,
            run_id="run-1",
            watchlist_id="ai_core",
            ticker_rows=[
                {
                    "ticker": "09988.HK",
                    "status": "candidate_shadow",
                    "promotion_debugger": {
                        "blocking_factors": [
                            {"code": "fundamentals_snapshot_fresh_or_explainable", "required_fix": "extract missing HK fields"}
                        ]
                    },
                    "fundamentals_missing_fields": ["gross_profit", "capex"],
                }
            ],
        )
        record_live_run_history(
            conn,
            run_id="run-2",
            watchlist_id="ai_core",
            ticker_rows=[
                {
                    "ticker": "09988.HK",
                    "status": "candidate_shadow",
                    "promotion_debugger": {
                        "blocking_factors": [
                            {"code": "fundamentals_snapshot_fresh_or_explainable", "required_fix": "extract missing HK fields"},
                            {"code": "consensus_proxy_quality"},
                        ]
                    },
                    "fundamentals_missing_fields": ["gross_profit", "capex"],
                },
                {"ticker": "00700.HK", "status": "observation_only", "promotion_debugger": {"blocking_factors": [{"code": "news_health"}]}},
            ],
        )

        runs = __import__("smr_live_run_history").list_live_run_history(conn, watchlist_id="ai_core", limit=10)
        triage = aggregate_blockers(runs, watchlist_id="ai_core")
        tasks = upsert_queue_from_triage(conn, triage)

        self.assertEqual(triage["run_count"], 2)
        self.assertEqual(triage["top_repeated_blockers"][0]["blocker_code"], "FUNDAMENTALS_MISSING_FIELDS")
        self.assertIn("09988.HK", triage["ticker_blocker_summary"])
        self.assertGreaterEqual(len(tasks), 3)
        self.assertGreaterEqual(len(list_repair_tasks(conn, status="open")), 3)


if __name__ == "__main__":
    unittest.main()
