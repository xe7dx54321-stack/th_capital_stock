import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase36_300394_evidence_repair_plan import build_payload, render_markdown


class Phase36300394EvidenceRepairPlanTests(unittest.TestCase):
    def test_repair_plan_is_planning_only_and_does_not_write_fake_evidence(self):
        payload = build_payload(sqlite3.connect(":memory:"))
        plan = payload["evidence_repair_plan"]
        self.assertEqual(plan["repair_goal"], "restore usable evidence chain before deeper research")
        self.assertGreaterEqual(len(plan["recommended_steps"]), 4)
        for step in plan["recommended_steps"]:
            self.assertTrue(step["expected_result"])
            self.assertNotIn("--execute", step["command_hint"])
        self.assertIn("do not fabricate evidence", plan["do_not_do"])
        self.assertIn("do not create pending", plan["do_not_do"])
        self.assertFalse(payload["safety"]["repair_executed"])
        self.assertFalse(payload["safety"]["fake_evidence_written"])
        self.assertIn("Phase 36 300394 Evidence Repair Plan", render_markdown(payload))


if __name__ == "__main__":
    unittest.main()
