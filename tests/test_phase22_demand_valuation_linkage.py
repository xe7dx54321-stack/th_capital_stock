import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_demand_valuation_linkage import build_demand_valuation_linkage


class Phase22DemandValuationLinkageTests(unittest.TestCase):
    def test_management_guidance_is_at_most_medium_support(self):
        payload = build_demand_valuation_linkage(
            sqlite3.connect(":memory:"),
            "TEST.SZ",
            demand_items=[
                {
                    "evidence_id": "ev_guidance",
                    "evidence_category": "management_guidance",
                    "demand_strength": "medium_indication",
                    "source_quality": "high",
                    "demand_direction": "positive",
                    "is_management_commentary": True,
                    "usable_for_proxy_signal": True,
                    "usable_for_bear_case_mitigation": True,
                    "independent_source_key": "filing_1",
                    "limitations": ["management commentary, not signed order"],
                }
            ],
        )

        linkage = payload["demand_valuation_linkage"]
        self.assertEqual(linkage["status"], "medium_support")
        self.assertIn("revenue_growth_assumption", linkage["supported_assumptions"])
        self.assertIn("no confirmed order", linkage["limitations"])

    def test_tender_award_can_be_strong_support(self):
        payload = build_demand_valuation_linkage(
            sqlite3.connect(":memory:"),
            "TEST.SZ",
            demand_items=[
                {
                    "evidence_id": "ev_tender",
                    "evidence_category": "tender_award",
                    "demand_strength": "confirmed_order",
                    "source_quality": "medium",
                    "demand_direction": "positive",
                    "usable_for_proxy_signal": True,
                    "usable_for_bear_case_mitigation": True,
                    "independent_source_key": "tender_1",
                    "limitations": [],
                }
            ],
        )

        self.assertEqual(payload["demand_valuation_linkage"]["status"], "strong_support")


if __name__ == "__main__":
    unittest.main()
