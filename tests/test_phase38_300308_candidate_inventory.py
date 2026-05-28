import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase38_300308_candidate_inventory import build_payload
from phase38_helpers import make_phase38_conn


class Phase38300308CandidateInventoryTests(unittest.TestCase):
    def test_inventory_tracks_phase37_candidates_by_variable(self):
        payload = build_payload(make_phase38_conn())
        inventory = payload["candidate_inventory"]
        self.assertEqual(inventory["candidates_total"], 15)
        self.assertGreaterEqual(inventory["by_variable"].get("product_mix", 0), 3)
        first = inventory["candidates"][0]
        self.assertTrue(first["candidate_id"])
        self.assertTrue(first["source_url"])
        self.assertTrue(first["quoted_span"])
        self.assertFalse(payload["safety"]["evidence_written"])


if __name__ == "__main__":
    unittest.main()
