import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "jobs", ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase38_300394_repair_queue_summary import build_payload as build_summary
from upsert_phase38_300394_repair_tasks import build_payload as upsert_tasks
from phase38_helpers import make_phase38_conn


class Phase38300394RepairQueueTests(unittest.TestCase):
    def test_repair_queue_hardening_writes_tasks_without_fake_evidence(self):
        conn = make_phase38_conn()
        upsert = upsert_tasks(conn, mode="execute")["repair_queue_upsert"]
        self.assertEqual(upsert["repair_tasks_written"], 5)
        summary = build_summary(conn)["repair_queue_summary"]
        self.assertEqual(summary["repair_tasks_written"], 5)
        self.assertFalse(summary["research_deepening_allowed"])
        self.assertTrue(all((task.get("metadata") or {}).get("fake_evidence_written") is False for task in summary["repair_tasks"]))


if __name__ == "__main__":
    unittest.main()
