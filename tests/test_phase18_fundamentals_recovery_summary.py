import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
for rel in [("08_scripts", "lib"), ("08_scripts", "reporting"), ("08_scripts", "verification"), ("08_scripts", "jobs")]:
    path = ROOT.joinpath(*rel)
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import build_phase18_fundamentals_recovery_summary as summary


class Phase18FundamentalsRecoverySummaryTests(unittest.TestCase):
    def test_summary_outputs_recovered_fields_and_markdown(self):
        fake_payload = {
            "generated_at": "now",
            "summary": {"source_gaps_closed": 1, "fields_recovered": 2, "fundamentals_snapshots_updated": 1, "core_blockers_reduced": 2, "new_pending_created": 0},
            "ticker_results": [{"ticker": "300308.SZ", "core_blockers_before": ["revenue", "gross_profit"], "core_blockers_after": [], "remaining_reason": "other_existing_gate_or_manual_review"}],
            "fundamentals_update": {
                "results": [
                    {
                        "ticker": "300308.SZ",
                        "fundamentals_snapshot_update": {
                            "fields_updated": [
                                {"field": "revenue", "status": "extracted", "source_evidence_id": "ev_rev", "allowed_usage": "supporting_evidence"}
                            ]
                        },
                    }
                ]
            },
        }
        with patch.object(summary, "build_payload", return_value=fake_payload):
            payload = summary.compact_summary(summary.build_payload(":memory:", ["300308.SZ"], live=False))
        self.assertEqual(payload["summary"]["fields_recovered"], 2)
        self.assertEqual(payload["recovered_fields"][0]["field"], "revenue")
        self.assertIn("Phase 18 Fundamentals Recovery Summary", summary.to_markdown(payload))


if __name__ == "__main__":
    unittest.main()
