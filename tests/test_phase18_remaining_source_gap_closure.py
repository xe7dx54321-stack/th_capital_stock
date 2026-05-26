import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
for rel in [("08_scripts", "lib"), ("08_scripts", "jobs"), ("08_scripts", "verification")]:
    path = ROOT.joinpath(*rel)
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import validate_phase18_remaining_source_gap_closure as validator


class Phase18RemainingSourceGapClosureTests(unittest.TestCase):
    def test_688041_source_found_refines_and_repairs_fields(self):
        fake_linkage = {
            "source_found": True,
            "source_id": "cninfo_688041_fixture",
            "chunks_found": 1,
            "evidence_linked_count": 1,
            "extraction": {"chunks": [{"section_type": "income_statement"}]},
        }
        fake_recovery = {
            "field_repair": {
                "revenue": {"status": "extracted", "source_evidence_id": "ev_revenue"},
                "gross_profit": {"status": "derived", "input_evidence_ids": ["ev_revenue", "ev_cost"]},
            }
        }
        with patch.object(validator, "link_payload", return_value=fake_linkage), patch.object(validator, "build_recovery_payload", return_value=fake_recovery), patch.object(validator, "register_snapshot"):
            result = validator.validate_ticker(":memory:", "688041.SH", live=False)
        self.assertEqual(set(result["fields_repaired"]), {"revenue", "gross_profit"})
        self.assertIn("financial_statement_source_not_found", result["blockers_resolved"])
        self.assertEqual(result["blockers_remaining"], [])

    def test_source_missing_does_not_fabricate_fields(self):
        fake_linkage = {"source_found": False, "chunks_found": 0, "evidence_linked_count": 0, "missing_reason": "cninfo_org_id_missing", "extraction": {"chunks": []}}
        fake_recovery = {"field_repair": {"revenue": {"status": "missing", "missing_reason": "field_not_found"}, "gross_profit": {"status": "missing", "missing_reason": "field_not_found"}}}
        with patch.object(validator, "link_payload", return_value=fake_linkage), patch.object(validator, "build_recovery_payload", return_value=fake_recovery), patch.object(validator, "register_snapshot"):
            result = validator.validate_ticker(":memory:", "688041.SH", live=False)
        self.assertEqual(result["fields_repaired"], [])
        self.assertEqual(set(result["blockers_remaining"]), {"revenue", "gross_profit"})


if __name__ == "__main__":
    unittest.main()
