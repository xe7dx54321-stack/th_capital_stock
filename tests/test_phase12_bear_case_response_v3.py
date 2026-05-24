import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_bear_case_response import respond_to_bear_case


class Phase12BearCaseResponseV3Tests(unittest.TestCase):
    def test_data_quality_bear_case_uses_field_evidence_quality(self):
        response = respond_to_bear_case(
            "09988.HK",
            {"bear_case_claims": [{"claim_text": "fundamentals data quality remains weak", "severity": "high"}]},
            fundamentals_snapshot={
                "field_details": {
                    f"field_{idx}": {"allowed_usage": "promotion_evidence", "source_evidence_id": f"ev_{idx}"}
                    for idx in range(5)
                }
            },
        )

        self.assertEqual(response["overall_response_status"], "partially_mitigated")
        self.assertEqual(response["responses"][0]["evidence_quality"], "promotion_evidence")

    def test_context_only_evidence_does_not_mitigate_core_bear_case(self):
        response = respond_to_bear_case(
            "09988.HK",
            {"bear_case_claims": [{"claim_text": "fundamentals data quality remains weak", "severity": "high"}]},
            fundamentals_snapshot={
                "field_details": {
                    f"field_{idx}": {"allowed_usage": "context_only", "source_evidence_id": None}
                    for idx in range(5)
                }
            },
        )

        self.assertEqual(response["overall_response_status"], "unresolved")


if __name__ == "__main__":
    unittest.main()

