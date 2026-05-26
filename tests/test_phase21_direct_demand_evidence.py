import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_direct_demand_evidence import classify_demand_evidence


class Phase21DirectDemandEvidenceTests(unittest.TestCase):
    def test_management_commentary_is_not_confirmed_order(self):
        item = classify_demand_evidence(
            {
                "evidence_id": "ev_guidance",
                "source_key": "annual_report",
                "source_type": "filing",
                "source_quality": "primary",
                "text_excerpt": "公司预计AI服务器和数据中心需求持续增长，客户认可度提升。",
                "metadata": {"source_id": "filing_2025", "chunk_section_type": "management_discussion"},
            },
            ticker="TEST.SZ",
        )

        self.assertEqual(item["evidence_category"], "downstream_capex")
        self.assertNotEqual(item["demand_strength"], "confirmed_order")
        self.assertFalse(item["usable_for_promotion"])
        self.assertIn("management commentary, not signed order", item["limitations"])

    def test_rumor_is_blocked(self):
        item = classify_demand_evidence(
            {
                "evidence_id": "ev_rumor",
                "source_key": "forum",
                "source_type": "news",
                "source_quality": "weak",
                "text_excerpt": "Rumor says a customer order may arrive, but this is unconfirmed.",
                "metadata": {"news_id": "rumor_1"},
            },
            ticker="TEST.SZ",
        )

        self.assertEqual(item["evidence_category"], "rumor_or_unconfirmed")
        self.assertEqual(item["demand_strength"], "blocked")
        self.assertFalse(item["usable_for_proxy_signal"])

    def test_missing_evidence_id_is_blocked(self):
        item = classify_demand_evidence(
            {
                "source_key": "annual_report",
                "source_type": "filing",
                "source_quality": "primary",
                "text_excerpt": "signed contract for AI server demand with key customer",
                "metadata": {"source_id": "filing_1"},
            },
            ticker="TEST.SZ",
        )

        self.assertEqual(item["demand_strength"], "blocked")
        self.assertIn("missing evidence_id", item["limitations"])


if __name__ == "__main__":
    unittest.main()
