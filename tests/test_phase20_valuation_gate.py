import sqlite3
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_valuation_gate import diagnose_valuation_gate


class Phase20ValuationGateTests(unittest.TestCase):
    def test_context_only_valuation_blocks_pending(self):
        with patch(
            "smr_valuation_gate.latest_valuation_snapshot",
            return_value={
                "valuation_available": True,
                "current_price": 10.0,
                "allowed_usage": "context_only",
                "valuation_confidence": 0.5,
                "peer_comparison": {"peer_comparison_status": "missing"},
                "historical_valuation": {"status": "missing"},
                "metadata": {"forward_eps": {"status": "missing", "is_official_consensus": False}},
            },
        ):
            payload = diagnose_valuation_gate(sqlite3.connect(":memory:"), "TEST.SZ", phase19_diag={})

        gate = payload["valuation_gate"]
        self.assertEqual(gate["after_status"], "context_only")
        self.assertTrue(gate["blocks_pending"])

    def test_supporting_valuation_allows_reduced_size_only(self):
        with patch(
            "smr_valuation_gate.latest_valuation_snapshot",
            return_value={
                "valuation_available": True,
                "current_price": 10.0,
                "allowed_usage": "supporting_evidence",
                "valuation_confidence": 0.7,
                "peer_comparison": {"peer_comparison_status": "supporting"},
                "historical_valuation": {"status": "available"},
                "metadata": {"forward_eps": {"status": "proxy", "is_official_consensus": False, "source_evidence_ids": []}},
            },
        ):
            payload = diagnose_valuation_gate(sqlite3.connect(":memory:"), "TEST.SZ", phase19_diag={})

        gate = payload["valuation_gate"]
        self.assertEqual(gate["after_status"], "supporting_evidence")
        self.assertFalse(gate["blocks_pending"])
        self.assertTrue(gate["allows_reduced_size_pending"])
        self.assertIn("FORWARD_EPS_PROXY_ONLY", gate["remaining_valuation_blockers"])
        self.assertTrue(gate["proxy_eps_not_official_consensus"])


if __name__ == "__main__":
    unittest.main()
