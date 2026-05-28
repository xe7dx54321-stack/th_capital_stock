import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "verification", ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from phase41_helpers import make_phase41_conn_with_followups
from validate_phase41_research_only_revalidation import build_payload


class Phase41ResearchOnlyRevalidationTests(unittest.TestCase):
    def test_revalidation_passes_without_confirmations_or_pending(self):
        payload = build_payload(make_phase41_conn_with_followups())
        summary = payload["summary"]
        self.assertEqual(payload["overall_status"], "pass")
        self.assertEqual(summary["specific_evidence_requests_created"], 3)
        self.assertFalse(summary["official_consensus_confirmed"])
        self.assertFalse(summary["supplier_share_confirmed"])
        self.assertFalse(summary["customer_allocation_confirmed"])
        self.assertEqual(summary["pending_created"], 0)
        self.assertEqual(summary["paper_order_created"], 0)


if __name__ == "__main__":
    unittest.main()
