import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "verification", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase39_300308_evidence_strengthened_packet import build_payload
from phase39_helpers import make_phase39_conn


class Phase39EvidenceStrengthenedPacketTests(unittest.TestCase):
    def test_packet_has_before_after_and_no_trade_advice(self):
        payload = build_payload(make_phase39_conn())
        packet = payload["evidence_strengthened_packet"]
        self.assertEqual(packet["new_evidence_written"], 5)
        self.assertGreater(packet["evidence_after"], packet["evidence_before"])
        self.assertFalse(packet["promotion_boundary"]["promotion_allowed"])
        self.assertIn("supplier share unconfirmed", packet["remaining_uncertainties"])
        text = json.dumps(payload, ensure_ascii=False).lower()
        self.assertNotIn("buy recommendation", text)
        self.assertNotIn("sell recommendation", text)
        self.assertNotIn("target price", text)
        self.assertNotIn("position guidance", text)


if __name__ == "__main__":
    unittest.main()
