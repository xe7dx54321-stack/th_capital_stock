import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_field_evidence_linkage import collect_field_evidence_ids, link_field_evidence
from smr_fundamentals_confidence import score_fundamental_field


class Phase12FieldEvidenceLinkageTests(unittest.TestCase):
    def test_field_source_map_attaches_evidence(self):
        linked = link_field_evidence(
            {"shareholders_equity": {"field": "shareholders_equity", "extracted_value": 100.0}},
            field_source_map={"shareholders_equity": "ev_equity"},
            source_metadata={"source_filing_id": "filing_1", "source_section_type": "balance_sheet"},
        )

        detail = linked["shareholders_equity"]
        self.assertEqual(detail["source_evidence_id"], "ev_equity")
        self.assertEqual(detail["source_filing_id"], "filing_1")
        self.assertIn("ev_equity", collect_field_evidence_ids(linked))

    def test_missing_evidence_stays_context_only(self):
        detail = {
            "field": "gross_profit",
            "extracted_value": 100.0,
            "unit_confidence": 0.95,
            "confidence": 0.82,
            "period": "FY2025",
            "missing_reason": None,
        }

        scored = score_fundamental_field("gross_profit", detail, source_quality="primary")

        self.assertEqual(scored["allowed_usage"], "context_only")


if __name__ == "__main__":
    unittest.main()

