import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
if str(REPORTING_DIR) not in sys.path:
    sys.path.insert(0, str(REPORTING_DIR))

from build_phase21_proxy_source_expansion import expand_proxy_snapshot_with_demand


class Phase21ProxySourceExpansionTests(unittest.TestCase):
    def test_demand_evidence_expands_independent_source_count_without_official_consensus(self):
        conn = sqlite3.connect(":memory:")
        base = {
            "proxy_direction": "up",
            "confidence": 0.5,
            "evidence_ids": ["ev_base"],
            "evidence_count": 1,
            "independent_source_count": 1,
            "signals": [{"direction": "up", "source_evidence_id": "ev_base"}],
        }
        demand_items = [
            {
                "demand_evidence_id": "demand_1",
                "evidence_id": "ev_demand",
                "demand_direction": "positive",
                "demand_strength": "medium_indication",
                "source_quality": "medium",
                "independent_source_key": "filing_2",
                "usable_for_proxy_signal": True,
            }
        ]

        expanded, added = expand_proxy_snapshot_with_demand(conn, ticker="TEST.SZ", base_snapshot=base, demand_items=demand_items)

        self.assertEqual(expanded["independent_source_count"], 2)
        self.assertEqual(added["independent_sources_added"], 1)
        self.assertIn("ev_demand", expanded["direct_demand_evidence_ids"])
        self.assertTrue(added["internal_proxy"])

    def test_metadata_does_not_count_as_independent_source(self):
        conn = sqlite3.connect(":memory:")
        expanded, _ = expand_proxy_snapshot_with_demand(
            conn,
            ticker="TEST.SZ",
            base_snapshot={"proxy_direction": "up", "confidence": 0.5, "evidence_ids": [], "independent_source_count": 0, "signals": []},
            demand_items=[
                {
                    "demand_evidence_id": "demand_meta",
                    "evidence_id": "ev_meta",
                    "demand_direction": "positive",
                    "demand_strength": "medium_indication",
                    "source_quality": "medium",
                    "independent_source_key": "watchlist_metadata_patch",
                    "usable_for_proxy_signal": True,
                }
            ],
        )

        self.assertEqual(expanded["independent_source_count"], 0)


if __name__ == "__main__":
    unittest.main()
