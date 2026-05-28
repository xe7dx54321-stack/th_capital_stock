import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase39_next_evidence_priority_update import build_payload
from phase39_helpers import make_phase39_conn


class Phase39NextEvidencePriorityTests(unittest.TestCase):
    def test_priority_keeps_sensitive_caveats(self):
        payload = build_payload(make_phase39_conn(), "300308.SZ")
        body = payload["next_evidence_priority_update"]
        remaining = {item["variable"]: item for item in body["remaining_high_priority"]}
        self.assertIn("product_mix", body["completed_or_improved"])
        self.assertEqual(remaining["supplier_share"]["priority"], "high_but_low_public_availability")
        self.assertEqual(remaining["official_consensus"]["recommended_mode"], "authorized_source_required")
        self.assertTrue(payload["safety"]["supplier_share_public_availability_caveat"])
        self.assertTrue(payload["safety"]["official_consensus_requires_authorized_source"])


if __name__ == "__main__":
    unittest.main()
