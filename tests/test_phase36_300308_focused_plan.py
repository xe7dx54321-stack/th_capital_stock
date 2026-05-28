import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase36_300308_focused_evidence_plan import build_payload, render_markdown
from phase34_helpers import make_phase34_conn


class Phase36300308FocusedPlanTests(unittest.TestCase):
    def test_focused_plan_targets_quality_not_pending(self):
        payload = build_payload(make_phase34_conn())
        plan = payload["focused_evidence_plan"]
        self.assertEqual(payload["ticker"], "300308.SZ")
        self.assertEqual(plan["target_quality"], "medium")
        self.assertEqual(plan["target_status"], "stronger_research_packet_not_pending")
        for variable in ("supplier_share", "ASP_price_proxy", "customer_allocation_proxy", "official_consensus"):
            self.assertIn(variable, plan["critical_gaps"])
        self.assertGreaterEqual(len(plan["priority_tasks"]), 4)
        self.assertEqual(payload["safety"]["new_pending_created"], 0)
        self.assertFalse(payload["safety"]["promotion_rules_relaxed"])
        self.assertIn("Why Not Pending After Plan", render_markdown(payload))


if __name__ == "__main__":
    unittest.main()
