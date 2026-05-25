import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
VERIFICATION_DIR = ROOT / "08_scripts" / "verification"
for path in (LIB_DIR, VERIFICATION_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from smr_registry import register_snapshot
from validate_phase15_core_blocker_recovery import build_recovery_payload


class Phase15CoreBlockerRecoveryTests(unittest.TestCase):
    def seed_phase14(self, conn):
        register_snapshot(
            conn,
            entity_type="phase14_thesis_aware_multi_ticker_live_validation",
            entity_id="ai_core",
            status="partial_pass",
            source="test",
            payload={
                "watchlist_id": "ai_core",
                "tickers": [
                    {
                        "ticker": "00700.HK",
                        "primary_thesis_type": "valuation_rerating",
                        "before_status": "candidate_shadow",
                        "after_status": "candidate_shadow",
                        "core_blockers": ["shareholders_equity"],
                    },
                    {
                        "ticker": "300308.SZ",
                        "primary_thesis_type": "ai_infrastructure_demand",
                        "before_status": "candidate_shadow",
                        "after_status": "candidate_shadow",
                        "core_blockers": ["revenue", "gross_profit"],
                    },
                ],
            },
        )

    def test_00700_core_blocker_has_before_after_and_missing_reason(self):
        conn = sqlite3.connect(":memory:")
        self.seed_phase14(conn)

        payload = build_recovery_payload(conn, "00700.HK")

        self.assertEqual(payload["core_blockers_before"], ["shareholders_equity"])
        self.assertIn("shareholders_equity", payload["field_repair"])
        self.assertIn(payload["field_repair"]["shareholders_equity"]["status"], {"missing", "extracted"})

    def test_a_share_core_blockers_have_diagnostics(self):
        conn = sqlite3.connect(":memory:")
        self.seed_phase14(conn)

        payload = build_recovery_payload(conn, "300308.SZ")

        self.assertIn("revenue", payload["core_blockers_before"])
        self.assertTrue(payload["minimum_fix_path"])
        self.assertIn("missing_reason", payload["field_status"]["revenue"])


if __name__ == "__main__":
    unittest.main()
