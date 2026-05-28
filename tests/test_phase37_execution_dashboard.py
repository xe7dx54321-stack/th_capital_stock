import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "jobs", ROOT / "08_scripts" / "verification", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase37_execution_dashboard import build_payload, render_markdown
from phase37_helpers import make_phase37_conn


class Phase37ExecutionDashboardTests(unittest.TestCase):
    def test_dashboard_reports_execution_without_pending_or_advice(self):
        payload = build_payload(make_phase37_conn())
        summary = payload["summary"]
        self.assertEqual(summary["300308_tasks_selected"], 5)
        self.assertEqual(summary["new_pending_created"], 0)
        self.assertEqual(summary["paper_order_created"], 0)
        self.assertFalse(payload["safety"]["dashboard_is_investment_advice"])
        self.assertIn("Phase 37 Execution Dashboard", render_markdown(payload))


if __name__ == "__main__":
    unittest.main()
