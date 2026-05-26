import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
for rel in [("08_scripts", "lib"), ("08_scripts", "jobs"), ("08_scripts", "verification")]:
    path = ROOT.joinpath(*rel)
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import validate_phase18_fundamentals_recovery_revalidation as validator


class Phase18FundamentalsRecoveryRevalidationTests(unittest.TestCase):
    def test_revalidation_reports_before_after_and_no_pending(self):
        fake_update = {
            "results": [
                {
                    "ticker": "300308.SZ",
                    "source_linkage": {"source_found": True, "chunks_found": 1, "evidence_linked_count": 1},
                    "fundamentals_snapshot_update": {"status": "updated", "snapshot_id": "snap", "fields_updated": [{"field": "revenue"}, {"field": "gross_profit"}]},
                    "snapshot": {
                        "revenue": 100.0,
                        "gross_profit": 30.0,
                        "field_details": {
                            "revenue": {"source_evidence_id": "ev_rev", "confidence": 0.82, "allowed_usage": "supporting_evidence"},
                            "gross_profit": {"source_evidence_id": "ev_rev", "input_evidence_ids": ["ev_rev", "ev_cost"], "confidence": 0.74, "allowed_usage": "supporting_evidence"},
                        },
                    },
                }
            ],
            "summary": {"fields_updated": 2},
        }
        with patch.object(validator, "update_payload", return_value=fake_update), patch.object(validator, "register_snapshot"):
            payload = validator.build_payload(":memory:", ["300308.SZ"], live=False)
        self.assertEqual(payload["summary"]["fields_recovered"], 2)
        self.assertEqual(payload["summary"]["new_pending_created"], 0)
        self.assertEqual(payload["ticker_results"][0]["core_blockers_after"], [])


if __name__ == "__main__":
    unittest.main()
