import sqlite3
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_valuation_gate_v2 import diagnose_valuation_gate_v2


class Phase22ValuationGateV2Tests(unittest.TestCase):
    def test_context_only_valuation_still_blocks_pending(self):
        with patch("smr_valuation_gate_v2.build_ticker_block_diagnostics", return_value={"primary_thesis_type": "ai_infrastructure_demand"}), patch(
            "smr_valuation_gate_v2.diagnose_valuation_gate",
            return_value={"valuation_gate": {"after_status": "context_only", "valuation_components": {"evidence_quality": "medium"}, "remaining_valuation_blockers": []}},
        ), patch(
            "smr_valuation_gate_v2.latest_valuation_snapshot",
            return_value={
                "current_price": 10,
                "allowed_usage": "context_only",
                "valuation_confidence": 0.65,
                "peer_comparison": {"peer_comparison_status": "supporting"},
                "historical_valuation": {"status": "available"},
                "metadata": {"inputs_used": {"forward_eps": {"status": "proxy", "is_official_consensus": False}}},
            },
        ), patch(
            "smr_valuation_gate_v2.build_demand_valuation_linkage",
            return_value={"demand_valuation_linkage": {"status": "medium_support"}},
        ):
            payload = diagnose_valuation_gate_v2(sqlite3.connect(":memory:"), "TEST.SZ")

        gate = payload["valuation_gate_v2"]
        self.assertEqual(gate["after_status"], "context_only")
        self.assertTrue(gate["blocks_pending"])

    def test_supporting_with_demand_can_be_reduced_size_supporting_only(self):
        with patch("smr_valuation_gate_v2.build_ticker_block_diagnostics", return_value={"primary_thesis_type": "ai_infrastructure_demand"}), patch(
            "smr_valuation_gate_v2.diagnose_valuation_gate",
            return_value={"valuation_gate": {"after_status": "supporting_evidence", "valuation_components": {"evidence_quality": "medium"}, "remaining_valuation_blockers": []}},
        ), patch(
            "smr_valuation_gate_v2.latest_valuation_snapshot",
            return_value={
                "current_price": 10,
                "allowed_usage": "supporting_evidence",
                "valuation_confidence": 0.7,
                "peer_comparison": {"peer_comparison_status": "supporting"},
                "historical_valuation": {"status": "available"},
                "metadata": {"inputs_used": {"forward_eps": {"status": "proxy", "is_official_consensus": False}}},
                "fundamentals_snapshot": {"revenue": 100, "net_profit": 10},
            },
        ), patch(
            "smr_valuation_gate_v2.build_demand_valuation_linkage",
            return_value={"demand_valuation_linkage": {"status": "medium_support"}},
        ):
            payload = diagnose_valuation_gate_v2(sqlite3.connect(":memory:"), "TEST.SZ")

        gate = payload["valuation_gate_v2"]
        self.assertEqual(gate["after_status"], "reduced_size_supporting")
        self.assertTrue(gate["allows_reduced_size_pending"])
        self.assertIn("FORWARD_EPS_PROXY_ONLY", gate["remaining_blockers"])
        self.assertFalse(gate["promotion_metadata"]["proxy_eps_is_official_consensus"])


if __name__ == "__main__":
    unittest.main()
