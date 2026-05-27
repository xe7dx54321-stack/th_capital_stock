import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
for path in (LIB_DIR, REPORTING_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase31_download_repair_queue_summary import build_payload, render_markdown
from smr_download_repair_queue import list_download_repair_tasks, upsert_download_repair_task


class Phase31DownloadRepairQueueTests(unittest.TestCase):
    def test_upsert_dedupes_repair_task_and_summary_outputs(self):
        conn = sqlite3.connect(":memory:")
        source = {
            "source_id": "ir_300394_missing",
            "ticker": "300394.SZ",
            "source_url": "https://static.cninfo.com.cn/missing.pdf",
            "repair_action": "manual_text_needed",
            "priority": "medium",
            "failure_reason": "download_unavailable",
        }
        upsert_download_repair_task(conn, source)
        upsert_download_repair_task(conn, source)
        self.assertEqual(len(list_download_repair_tasks(conn)), 1)
        payload = build_payload(conn)
        self.assertEqual(payload["summary"]["repair_tasks_total"], 1)
        self.assertIn("Phase 31 Download Repair Queue Summary", render_markdown(payload))


if __name__ == "__main__":
    unittest.main()
