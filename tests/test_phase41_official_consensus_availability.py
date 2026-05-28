import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase41_official_consensus_availability import build_payload
from phase41_helpers import make_phase41_conn_with_followups


class Phase41OfficialConsensusAvailabilityTests(unittest.TestCase):
    def test_internal_proxy_does_not_become_official_consensus(self):
        payload = build_payload(make_phase41_conn_with_followups(), "300308.SZ")
        body = payload["official_consensus_availability"]
        self.assertEqual(body["status"], "commercial_source_required")
        self.assertFalse(body["official_consensus_available"])
        self.assertFalse(body["official_consensus_confirmed"])
        self.assertEqual(body["internal_proxy_allowed_usage"], "supporting_context_only")
        self.assertIn("do not treat internal proxy as official consensus", body["do_not_do"])


if __name__ == "__main__":
    unittest.main()
