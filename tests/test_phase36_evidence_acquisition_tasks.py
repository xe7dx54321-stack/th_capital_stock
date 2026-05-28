import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase36_evidence_acquisition_tasks import build_payload, render_markdown
from phase34_helpers import make_phase34_conn


class Phase36EvidenceAcquisitionTasksTests(unittest.TestCase):
    def test_tasks_have_safety_caveats_and_expected_outputs(self):
        payload = build_payload(make_phase34_conn(), ticker="300308.SZ")
        tasks = payload["evidence_acquisition_tasks"]
        self.assertGreaterEqual(len(tasks), 7)
        for task in tasks:
            self.assertTrue(task["do_not_do"])
            self.assertIn("do not create pending", task["do_not_do"])
            if task["priority"] == "high":
                self.assertTrue(task["expected_output"])
        supplier_tasks = [task for task in tasks if task["variable"] == "supplier_share"]
        self.assertTrue(any(task["task_type"] == "MARK_NOT_PUBLICLY_CONFIRMABLE" for task in supplier_tasks))
        self.assertEqual(payload["summary"]["new_pending_created"], 0)
        self.assertFalse(payload["safety"]["fetch_executed"])
        self.assertIn("Phase 36 Evidence Acquisition Tasks", render_markdown(payload))


if __name__ == "__main__":
    unittest.main()
