import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "lib", ROOT / "08_scripts" / "reporting", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase34_post_governance_evidence_state import build_payload
from phase34_helpers import make_phase34_conn


class Phase34PostGovernanceEvidenceStateTests(unittest.TestCase):
    def test_approved_evidence_is_not_promotion_evidence(self):
        payload = build_payload(make_phase34_conn(), ticker="300394.SZ")
        self.assertEqual(payload["summary"]["approved_evidence"], 1)
        self.assertEqual(payload["summary"]["promotion_allowed_true"], 0)
        self.assertFalse(payload["safety"]["approved_evidence_is_promotion_evidence"])

    def test_rejected_and_noise_are_inactive(self):
        row = build_payload(make_phase34_conn(), ticker="300394.SZ")["ticker_results"][0]
        inactive = set(row["evidence_delta"]["inactive_evidence_ids"])
        self.assertIn("ev_rejected_end", inactive)
        self.assertIn("ev_noise", inactive)
        self.assertLess(row["evidence_state"]["active_semantic_evidence"], row["evidence_state"]["total_semantic_evidence"])


if __name__ == "__main__":
    unittest.main()
