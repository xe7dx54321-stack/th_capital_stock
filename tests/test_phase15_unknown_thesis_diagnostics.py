import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
for path in (LIB_DIR, REPORTING_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase15_unknown_thesis_diagnostics import build_ticker_payload
from smr_registry import register_snapshot


class Phase15UnknownThesisDiagnosticsTests(unittest.TestCase):
    def test_002230_unknown_thesis_has_reasons_and_patch(self):
        conn = sqlite3.connect(":memory:")
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
                        "ticker": "002230.SZ",
                        "primary_thesis_type": "unknown",
                        "thesis_inference_confidence": 0.29,
                        "data_quality_gate": "blocked",
                        "thesis_inference": {
                            "primary_thesis_type": "unknown",
                            "confidence": 0.29,
                            "signals_used": ["valuation_related_text"],
                            "scorecard": {"valuation_rerating": 0.22},
                            "inferred_thesis_types": [],
                        },
                    }
                ],
            },
        )

        payload = build_ticker_payload(conn, "002230.SZ")

        self.assertEqual(payload["current_thesis_type"], "unknown")
        self.assertFalse(payload["allow_pending"])
        self.assertIn("low_thesis_inference_confidence", payload["unknown_reasons"])
        self.assertIn("candidate_thesis_types", payload["suggested_metadata_patch"])


if __name__ == "__main__":
    unittest.main()
