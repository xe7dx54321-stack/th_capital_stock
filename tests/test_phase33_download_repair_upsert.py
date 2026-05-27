import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
JOBS_DIR = ROOT / "08_scripts" / "jobs"
VERIFICATION_DIR = ROOT / "08_scripts" / "verification"
for path in (LIB_DIR, JOBS_DIR, VERIFICATION_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from smr_download_repair_queue import upsert_download_repair_task
from validate_phase33_download_repair_upsert import build_payload
import sqlite3


class Phase33DownloadRepairUpsertTests(unittest.TestCase):
    def test_repair_task_upsert_dedupes_and_does_not_affect_promotion(self):
        conn = sqlite3.connect(":memory:")
        task = {
            "source_id": "ir_test_source",
            "ticker": "300394.SZ",
            "task_type": "MANUAL_TEXT_NEEDED",
            "priority": "medium",
            "source_url": "https://example.com/ir.pdf",
            "reason": "download_unavailable",
            "recommended_action": "manual_text_needed",
        }
        upsert_download_repair_task(conn, task)
        upsert_download_repair_task(conn, task)
        payload = build_payload(conn)
        self.assertEqual(payload["overall_status"], "pass")
        self.assertEqual(payload["summary"]["repair_tasks_written"], 1)
        self.assertEqual(payload["summary"]["duplicates_skipped"], 0)
        self.assertEqual(payload["summary"]["promotion_allowed_from_repair_tasks"], 0)


if __name__ == "__main__":
    unittest.main()
