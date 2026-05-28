import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase35_evidence_chain_packet import build_payload, render_markdown
from phase34_helpers import make_phase34_conn


class Phase35EvidenceChainTests(unittest.TestCase):
    def test_rejected_and_noise_do_not_enter_key_evidence(self):
        payload = build_payload(make_phase34_conn(), ticker="300394.SZ")
        chain = payload["evidence_chain"]
        lifecycle_statuses = {row["lifecycle_status"] for row in chain["key_evidence"]}
        self.assertNotIn("rejected_evidence", lifecycle_statuses)
        self.assertNotIn("marked_noise", lifecycle_statuses)
        self.assertGreaterEqual(chain["downgraded_evidence"], 1)
        markdown = render_markdown(payload)
        self.assertIn("Phase 35 Evidence Chain Packet", markdown)


if __name__ == "__main__":
    unittest.main()
