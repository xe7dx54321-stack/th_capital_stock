import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_thesis_inference import infer_thesis_type, thesis_inference_allows_auto_pending


class Phase14ThesisInferenceTests(unittest.TestCase):
    def test_09988_infers_valuation_rerating_from_valuation_support(self):
        result = infer_thesis_type(
            "09988.HK",
            candidate={"reason": "valuation discount rerating candidate"},
            valuation={
                "allowed_usage": "supporting_evidence",
                "peer_comparison": {"peer_comparison_status": "supporting"},
                "historical_valuation": {"status": "available"},
            },
            watchlist_item={"theme": "internet_platform", "sector": "internet_platform"},
        )

        self.assertEqual(result["primary_thesis_type"], "valuation_rerating")
        self.assertGreaterEqual(result["confidence"], 0.5)
        self.assertIn("peer_comparison_supporting", result["signals_used"])

    def test_cash_flow_terms_infer_cash_flow_improvement(self):
        result = infer_thesis_type("09988.HK", claims=[{"claim_text": "capex decline and FCF repair"}])

        self.assertEqual(result["primary_thesis_type"], "cash_flow_improvement")
        self.assertTrue(thesis_inference_allows_auto_pending(result))

    def test_unknown_thesis_requires_manual_review(self):
        result = infer_thesis_type("300308.SZ", candidate={"reason": "monitor unclear setup"})

        self.assertEqual(result["primary_thesis_type"], "unknown")
        self.assertTrue(result["needs_manual_thesis_review"])
        self.assertFalse(thesis_inference_allows_auto_pending(result))


if __name__ == "__main__":
    unittest.main()
