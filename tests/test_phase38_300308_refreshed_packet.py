import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "jobs", ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "verification", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase38_300308_refreshed_packet_after_persistence import build_payload
from persist_phase38_300308_targeted_candidates import build_payload as persist_candidates
from phase38_helpers import make_phase38_conn


class Phase38300308RefreshedPacketTests(unittest.TestCase):
    def test_refreshed_packet_has_before_after_and_no_trade_advice(self):
        conn = make_phase38_conn()
        persist_candidates(conn, mode="execute", limit=5)
        payload = build_payload(conn)
        packet = payload["refreshed_packet_after_persistence"]
        self.assertEqual(packet["new_evidence_written"], 5)
        self.assertFalse(packet["why_not_pending"]["promotion_allowed"])
        text = json.dumps(payload, ensure_ascii=False).lower()
        self.assertNotIn("target price", text)
        self.assertNotIn("position guidance", text)
        self.assertFalse(payload["safety"]["trade_recommendation_generated"])


if __name__ == "__main__":
    unittest.main()
