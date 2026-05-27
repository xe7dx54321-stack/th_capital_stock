import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
JOBS_DIR = ROOT / "08_scripts" / "jobs"
for path in (LIB_DIR, REPORTING_DIR, JOBS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase32_download_repair_workbench import build_payload, render_markdown
from smr_download_repair_queue import upsert_download_repair_task


class Phase32DownloadRepairWorkbenchTests(unittest.TestCase):
    def test_download_repair_packet_outputs_tasks(self):
        conn = sqlite3.connect(":memory:")
        upsert_download_repair_task(
            conn,
            {
                "source_id": "ir_300394_missing",
                "ticker": "300394.SZ",
                "source_url": "https://static.cninfo.com.cn/missing.pdf",
                "repair_action": "manual_text_needed",
                "priority": "medium",
                "failure_reason": "download_unavailable",
            },
        )
        payload = build_payload(conn)
        self.assertEqual(payload["summary"]["repair_tasks"], 1)
        self.assertEqual(payload["summary"]["manual_text_needed"], 1)
        self.assertIn("Do not bypass download restrictions", render_markdown(payload))


if __name__ == "__main__":
    unittest.main()
