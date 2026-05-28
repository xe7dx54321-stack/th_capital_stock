import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase35_why_not_pending import build_payload, render_markdown
from phase34_helpers import make_phase34_conn


class Phase35WhyNotPendingTests(unittest.TestCase):
    def test_why_not_pending_keeps_promotion_false_and_lists_core_reasons(self):
        payload = build_payload(make_phase34_conn(), ticker="300394.SZ")
        why = payload["why_not_pending"]
        self.assertFalse(why["promotion_allowed"])
        reasons = " ".join(why["core_reasons"])
        self.assertIn("supplier_share", reasons)
        self.assertIn("ASP_price_proxy", reasons)
        self.assertIn("customer_allocation", reasons)
        self.assertFalse(payload["safety"]["new_pending_created"])
        self.assertIn("Why Not Pending", render_markdown(payload))


if __name__ == "__main__":
    unittest.main()
