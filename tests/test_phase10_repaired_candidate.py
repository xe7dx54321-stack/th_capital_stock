import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
VERIFICATION_DIR = ROOT / "08_scripts" / "verification"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))
if str(VERIFICATION_DIR) not in sys.path:
    sys.path.insert(0, str(VERIFICATION_DIR))

from validate_phase10_repaired_candidate import valuation_summary


class Phase10RepairedCandidateTests(unittest.TestCase):
    def test_valuation_summary_outputs_required_phase10_fields(self):
        summary = valuation_summary(
            {
                "allowed_usage": "supporting_evidence",
                "valuation_status": "partial",
                "peer_set_id": "hk_internet_platforms",
                "peer_set_status": "partial",
                "historical_percentile_status": "missing",
                "forward_eps": {"status": "proxy", "source": "internal_proxy"},
            },
            {"price_status": "fresh", "sub_blockers": ["FORWARD_EPS_MISSING"]},
        )

        self.assertEqual(summary["peer_set_status"], "partial")
        self.assertEqual(summary["historical_percentile_status"], "missing")
        self.assertEqual(summary["forward_eps_status"], "proxy")


if __name__ == "__main__":
    unittest.main()
