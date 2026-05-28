import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "jobs", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from run_phase37_targeted_semantic_extraction import build_payload
from phase37_helpers import make_phase37_conn


class Phase37TargetedSemanticExtractionTests(unittest.TestCase):
    def test_extraction_keeps_quoted_span_and_sensitive_caveats(self):
        payload = build_payload(make_phase37_conn(), ticker="300308.SZ", dry_run=True)
        body = payload["targeted_semantic_extraction"]
        self.assertEqual(body["quoted_span_validated"], body["semantic_extractions"])
        self.assertEqual(body["invalid_extractions"], 0)
        asp_rows = [row for row in body["extractions"] if row["variable"] == "ASP_price_proxy"]
        customer_rows = [row for row in body["extractions"] if row["variable"] == "customer_allocation_proxy"]
        self.assertTrue(any("do not treat product mix as ASP" in row["limitations"] for row in asp_rows))
        self.assertTrue(any("does not confirm customer allocation" in row["limitations"] for row in customer_rows))
        self.assertFalse(payload["safety"]["product_mix_auto_converted_to_asp"])
        self.assertFalse(payload["safety"]["customer_demand_converted_to_confirmed_order"])


if __name__ == "__main__":
    unittest.main()
