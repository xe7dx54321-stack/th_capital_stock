import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase36_acquisition_readiness_score import build_payload, render_markdown
from phase34_helpers import make_phase34_conn


class Phase36AcquisitionReadinessTests(unittest.TestCase):
    def test_readiness_prioritizes_feasible_ir_over_unconfirmable_share(self):
        payload = build_payload(make_phase34_conn(), ticker="300308.SZ")
        rows = payload["acquisition_readiness"]
        asp_ir = next(row for row in rows if row["variable"] == "ASP_price_proxy" and row["task_type"] == "FIND_COMPANY_IR_EVIDENCE")
        supplier_manual = next(row for row in rows if row["variable"] == "supplier_share" and row["task_type"] == "MANUAL_RESEARCH_REQUIRED")
        supplier_not_public = next(row for row in rows if row["variable"] == "supplier_share" and row["task_type"] == "MARK_NOT_PUBLICLY_CONFIRMABLE")
        customer_ir = next(row for row in rows if row["variable"] == "customer_allocation_proxy" and row["task_type"] == "FIND_COMPANY_IR_EVIDENCE")
        self.assertGreater(asp_ir["readiness_score"], supplier_manual["readiness_score"])
        self.assertEqual(supplier_manual["readiness_bucket"], "manual_or_low_confidence")
        self.assertEqual(supplier_not_public["readiness_bucket"], "manual_or_low_confidence")
        self.assertNotEqual(customer_ir["readiness_bucket"], "high_priority")
        self.assertFalse(payload["safety"]["readiness_is_investment_rating"])
        self.assertIn("Phase 36 Acquisition Readiness Score", render_markdown(payload))


if __name__ == "__main__":
    unittest.main()
