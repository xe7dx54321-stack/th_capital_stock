import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_source_acquisition_plan import build_source_acquisition_plan_for_task


class Phase23SourceAcquisitionPlanTests(unittest.TestCase):
    def test_implemented_sources_are_ordered_before_planned(self):
        plan = build_source_acquisition_plan_for_task(
            {"task_type": "CONFIRMED_ORDER_EVIDENCE_MISSING", "priority": "high", "missing_evidence": "confirmed order missing"},
            ticker="300308.SZ",
            market="CN",
        )["source_acquisition_plan"]
        steps = plan["ordered_steps"]
        self.assertEqual(steps[0]["status"], "implemented")
        self.assertTrue(any(step["status"] == "planned" and not step["is_usable_now"] for step in steps))
        self.assertFalse(plan["planned_connectors_executed"])
        self.assertFalse(plan["writes_evidence_graph"])


if __name__ == "__main__":
    unittest.main()
