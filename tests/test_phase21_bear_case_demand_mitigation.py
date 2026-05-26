import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_bear_case_mitigation import map_bear_case_to_evidence


class Phase21BearCaseDemandMitigationTests(unittest.TestCase):
    def test_direct_demand_evidence_can_mitigate_core_demand_bear_case(self):
        payload = map_bear_case_to_evidence(
            sqlite3.connect(":memory:"),
            ticker="TEST.SZ",
            primary_thesis_type="ai_infrastructure_demand",
            claims=[
                {
                    "bear_case_claim_id": "bear_direct_demand",
                    "bear_case_text": "Direct AI order or customer demand evidence is missing.",
                    "risk_category": "competitive_risk",
                    "core_to_thesis": True,
                }
            ],
            fundamentals_snapshot={},
            direct_demand_evidence=[
                {
                    "evidence_id": "ev_demand",
                    "demand_strength": "medium_indication",
                    "source_quality": "high",
                    "claim_relevance": "core",
                    "usable_for_bear_case_mitigation": True,
                    "independent_source_key": "filing_1",
                }
            ],
        )

        gate = payload["bear_case_mitigation"]
        response = gate["responses"][0]
        self.assertEqual(response["after_status"], "partially_mitigated")
        self.assertIn("ev_demand", response["mitigating_evidence_ids"])
        self.assertFalse(gate["blocks_pending"])

    def test_low_quality_demand_evidence_cannot_mitigate_core_bear_case(self):
        payload = map_bear_case_to_evidence(
            sqlite3.connect(":memory:"),
            ticker="TEST.SZ",
            primary_thesis_type="ai_infrastructure_demand",
            claims=[
                {
                    "bear_case_claim_id": "bear_direct_demand",
                    "bear_case_text": "Direct AI order evidence is missing.",
                    "risk_category": "competitive_risk",
                    "core_to_thesis": True,
                }
            ],
            fundamentals_snapshot={},
            direct_demand_evidence=[
                {
                    "evidence_id": "ev_weak",
                    "demand_strength": "weak_indication",
                    "source_quality": "low",
                    "claim_relevance": "core",
                    "usable_for_bear_case_mitigation": False,
                    "independent_source_key": "news_1",
                }
            ],
        )

        response = payload["bear_case_mitigation"]["responses"][0]
        self.assertEqual(response["after_status"], "requires_more_evidence")
        self.assertTrue(payload["bear_case_mitigation"]["blocks_pending"])


if __name__ == "__main__":
    unittest.main()
