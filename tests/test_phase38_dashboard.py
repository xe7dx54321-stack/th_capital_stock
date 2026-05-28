import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "jobs", ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "verification", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase38_persistence_review_dashboard import build_payload
from persist_phase38_300308_targeted_candidates import build_payload as persist_candidates
from upsert_phase38_300394_repair_tasks import build_payload as upsert_repair
from phase38_helpers import make_phase38_conn


class Phase38DashboardTests(unittest.TestCase):
    def test_dashboard_reports_persistence_and_repair_without_pending(self):
        conn = make_phase38_conn()
        persist_candidates(conn, mode="execute", limit=5)
        upsert_repair(conn, mode="execute")
        payload = build_payload(conn)
        summary = payload["summary"]
        self.assertEqual(summary["300308_candidates_total"], 15)
        self.assertEqual(summary["candidates_written"], 5)
        self.assertEqual(summary["300394_repair_tasks_written"], 5)
        self.assertEqual(summary["new_pending_created"], 0)
        self.assertEqual(summary["promotion_allowed_true"], 0)
        self.assertFalse(payload["safety"]["real_trade_risk"])


if __name__ == "__main__":
    unittest.main()
