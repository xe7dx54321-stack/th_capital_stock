import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_proxy_signal_gate import evaluate_proxy_signal_gate


class Phase20ProxySignalGateTests(unittest.TestCase):
    def test_independent_source_count_below_two_cannot_be_strong(self):
        payload = evaluate_proxy_signal_gate(
            sqlite3.connect(":memory:"),
            "TEST.SZ",
            thesis_type="ai_infrastructure_demand",
            snapshot={
                "proxy_direction": "up",
                "confidence": 0.9,
                "evidence_ids": ["ev_one"],
                "evidence_count": 1,
                "independent_source_count": 1,
                "signals": [{"direction": "up", "source_evidence_id": "ev_one"}],
            },
        )

        gate = payload["proxy_signal_gate"]
        self.assertNotEqual(gate["status"], "strong")
        self.assertIn("independent_source_count>=2", gate["missing_requirements"])

    def test_proxy_is_never_official_consensus(self):
        payload = evaluate_proxy_signal_gate(
            sqlite3.connect(":memory:"),
            "TEST.SZ",
            thesis_type="ai_infrastructure_demand",
            snapshot={
                "proxy_direction": "up",
                "confidence": 0.9,
                "evidence_ids": ["ev_one", "ev_two"],
                "evidence_count": 2,
                "independent_source_count": 2,
                "signals": [{"direction": "up", "source_evidence_id": "ev_one"}],
            },
        )

        self.assertFalse(payload["proxy_signal_gate"]["is_official_consensus"])
        self.assertIn("internal proxy only", payload["proxy_signal_gate"]["note"])


if __name__ == "__main__":
    unittest.main()
