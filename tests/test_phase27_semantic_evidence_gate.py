import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_semantic_evidence_gate import gate_semantic_extraction
from smr_semantic_evidence_schema import make_semantic_extraction


class Phase27SemanticEvidenceGateTests(unittest.TestCase):
    def test_management_commentary_downgraded_and_missing_quote_blocked(self):
        item = make_semantic_extraction(
            ticker="300394.SZ",
            theme="ai_optical_interconnect",
            source_id="s1",
            chunk_id="c1",
            source_type="investor_relations_record",
            variable_type="order_visibility_signal",
            claim_text="需求旺盛",
            quoted_span="客户需求增长",
            evidence_strength="management_commentary",
            confidence="medium",
        )
        gated = gate_semantic_extraction(item, source_url="mock://s", chunk_text="客户需求增长")
        self.assertEqual(gated["evidence_status"], "partial")
        self.assertFalse(gated["usable_for_promotion"])
        blocked = gate_semantic_extraction(dict(item, quoted_span=""), source_url="mock://s")
        self.assertEqual(blocked["evidence_status"], "blocked")

    def test_industry_forecast_not_company_order(self):
        item = make_semantic_extraction(
            ticker="300394.SZ",
            theme="ai_optical_interconnect",
            source_id="i1",
            chunk_id="c1",
            source_type="industry_public_commentary",
            variable_type="industry_forecast_signal",
            claim_text="800G 光模块需求增长",
            quoted_span="800G 光模块需求增长",
            evidence_strength="industry_forecast",
            confidence="medium",
        )
        gated = gate_semantic_extraction(item, source_url="mock://i", chunk_text="800G 光模块需求增长")
        self.assertTrue(gated["usable_for_valuation_support"])
        self.assertFalse(gated["usable_for_promotion"])
        self.assertIn("industry forecast is not company order", gated["downgrade_reasons"])


if __name__ == "__main__":
    unittest.main()
