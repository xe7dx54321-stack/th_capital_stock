import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase39_300308_evidence_contribution import build_payload
from phase39_helpers import make_phase39_conn


class Phase39EvidenceContributionTests(unittest.TestCase):
    def test_new_evidence_contribution_tracks_boundaries(self):
        payload = build_payload(make_phase39_conn())
        body = payload["evidence_contribution"]
        self.assertEqual(body["new_evidence_count"], 5)
        self.assertIn("product_mix", body["variables_strengthened"])
        self.assertIn("order_visibility", body["variables_strengthened"])
        self.assertIn("shipment", body["variables_strengthened"])
        text = json.dumps(body, ensure_ascii=False).lower()
        self.assertIn("exact asp", text)
        self.assertIn("confirmed order", text)
        self.assertFalse(payload["safety"]["product_mix_converted_to_confirmed_asp"])
        self.assertFalse(payload["safety"]["order_visibility_converted_to_confirmed_order"])
        self.assertFalse(payload["safety"]["shipment_commentary_converted_to_number"])


if __name__ == "__main__":
    unittest.main()
