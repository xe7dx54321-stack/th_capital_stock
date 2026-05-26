import sqlite3
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
if str(REPORTING_DIR) not in sys.path:
    sys.path.insert(0, str(REPORTING_DIR))

from build_phase22_proxy_strengthening import build_ticker_proxy_strengthening, proxy_strengthened


class Phase22ProxyStrengtheningTests(unittest.TestCase):
    def test_proxy_strengthening_keeps_internal_proxy_label(self):
        with patch(
            "build_phase22_proxy_strengthening.build_ticker_proxy_source_expansion",
            return_value={
                "ticker": "TEST.SZ",
                "before": {"proxy_status": "weak", "independent_source_count": 1, "proxy_strength_score": 0.42},
                "after": {
                    "proxy_status": "medium",
                    "independent_source_count": 2,
                    "proxy_strength_score": 0.61,
                    "usable_for_reduced_size_pending": True,
                    "remaining_requirements": [],
                },
            },
        ), patch(
            "build_phase22_proxy_strengthening.extract_direct_demand_evidence",
            return_value=[
                {
                    "evidence_id": "ev_demand",
                    "independent_source_key": "source_2",
                    "source_quality": "medium",
                    "claim_relevance": "supporting",
                    "demand_strength": "medium_indication",
                    "usable_for_proxy_signal": True,
                }
            ],
        ):
            row = build_ticker_proxy_strengthening(sqlite3.connect(":memory:"), "TEST.SZ")

        gate = row["proxy_strengthening"]
        self.assertTrue(proxy_strengthened(row))
        self.assertFalse(gate["after"]["is_official_consensus"])
        self.assertTrue(gate["safety"]["internal_proxy_only"])


if __name__ == "__main__":
    unittest.main()
