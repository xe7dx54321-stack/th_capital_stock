import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "verification", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from validate_phase37_300308_post_acquisition_revalidation import build_payload
from phase37_helpers import make_phase37_conn


class Phase37300308PostAcquisitionRevalidationTests(unittest.TestCase):
    def test_revalidation_is_modest_and_does_not_create_pending(self):
        payload = build_payload(make_phase37_conn())
        body = payload["post_acquisition_revalidation"]
        self.assertIn(body["research_quality_delta"], {"modestly_strengthened", "unchanged_needs_more_data"})
        self.assertEqual(body["research_quality_after"], "medium_low")
        self.assertIn("supplier_share", body["still_missing_variables"])
        self.assertEqual(body["new_pending_created"], 0)
        self.assertFalse(payload["safety"]["investment_advice_generated"])


if __name__ == "__main__":
    unittest.main()
