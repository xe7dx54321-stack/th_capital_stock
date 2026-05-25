import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
for rel in [("08_scripts", "lib"), ("08_scripts", "jobs"), ("08_scripts", "verification")]:
    path = ROOT.joinpath(*rel)
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import validate_phase17_source_chunk_recovery as validator


class Phase17SourceChunkRecoveryValidatorTests(unittest.TestCase):
    def test_validator_reports_before_after_and_repaired_fields(self):
        fake_linkage = {
            "source_found": True,
            "source_id": "cninfo_300308_fixture",
            "chunks_found": 1,
            "evidence_linked_count": 1,
            "extraction": {"chunks": [{"section_type": "income_statement"}]},
        }
        fake_recovery = {
            "field_repair": {
                "revenue": {"status": "extracted", "source_evidence_id": "ev_revenue", "confidence": 0.82},
                "gross_profit": {"status": "derived", "input_evidence_ids": ["ev_revenue", "ev_cost"], "confidence": 0.74},
            }
        }
        with patch.object(validator, "link_payload", return_value=fake_linkage), patch.object(validator, "build_recovery_payload", return_value=fake_recovery):
            result = validator.validate_ticker(":memory:", "300308.SZ", live=False)
        self.assertTrue(result["source_recovery"]["income_statement_chunk_found"])
        self.assertEqual(set(result["fields_repaired"]), {"revenue", "gross_profit"})
        self.assertEqual(result["blockers_remaining"], [])


if __name__ == "__main__":
    unittest.main()
