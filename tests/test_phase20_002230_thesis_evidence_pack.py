import sqlite3
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
if str(REPORTING_DIR) not in sys.path:
    sys.path.insert(0, str(REPORTING_DIR))

from build_phase20_002230_thesis_evidence_pack import build_payload


class Phase20002230ThesisEvidencePackTests(unittest.TestCase):
    def test_metadata_only_does_not_create_pending(self):
        with patch(
            "build_phase20_002230_thesis_evidence_pack.build_phase19_thesis_gate",
            return_value={
                "before": {"primary_thesis_type": "unknown", "confidence": 0.29, "allow_pending": False},
                "after_metadata_simulation": {
                    "candidate_thesis_type": "ai_infrastructure_demand",
                    "confidence": 0.95,
                    "allow_pending": False,
                },
            },
        ), patch(
            "build_phase20_002230_thesis_evidence_pack.build_proxy_signal_gate",
            return_value={"proxy_signal_gate": {"status": "weak", "missing_requirements": ["dominant_proxy_signal"]}},
        ), patch(
            "build_phase20_002230_thesis_evidence_pack._claim_graph_support",
            return_value={"status": "missing", "claim_ids": [], "missing": ["claim_graph_support"]},
        ), patch(
            "build_phase20_002230_thesis_evidence_pack._filing_or_news_support",
            return_value={"status": "missing", "evidence_ids": [], "missing": ["filing_or_news_support"]},
        ):
            payload = build_payload(sqlite3.connect(":memory:"))

        self.assertEqual(payload["after"]["thesis_status"], "metadata_only_candidate")
        self.assertFalse(payload["after"]["allow_pending"])

    def test_evidence_backed_candidate_can_still_be_not_pending(self):
        with patch(
            "build_phase20_002230_thesis_evidence_pack.build_phase19_thesis_gate",
            return_value={
                "before": {"primary_thesis_type": "unknown", "confidence": 0.29, "allow_pending": False},
                "after_metadata_simulation": {
                    "candidate_thesis_type": "ai_infrastructure_demand",
                    "confidence": 0.95,
                    "allow_pending": False,
                },
            },
        ), patch(
            "build_phase20_002230_thesis_evidence_pack.build_proxy_signal_gate",
            return_value={"proxy_signal_gate": {"status": "weak", "missing_requirements": ["dominant_proxy_signal"]}},
        ), patch(
            "build_phase20_002230_thesis_evidence_pack._claim_graph_support",
            return_value={"status": "partial", "claim_ids": ["claim_1"], "missing": []},
        ), patch(
            "build_phase20_002230_thesis_evidence_pack._filing_or_news_support",
            return_value={"status": "partial", "evidence_ids": ["ev_1"], "missing": []},
        ):
            payload = build_payload(sqlite3.connect(":memory:"))

        self.assertEqual(payload["after"]["thesis_status"], "evidence_backed_candidate")
        self.assertFalse(payload["after"]["allow_pending"])


if __name__ == "__main__":
    unittest.main()
