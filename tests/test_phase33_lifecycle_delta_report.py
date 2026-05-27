import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
JOBS_DIR = ROOT / "08_scripts" / "jobs"
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
TEST_DIR = ROOT / "tests"
for path in (LIB_DIR, JOBS_DIR, REPORTING_DIR, TEST_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase33_lifecycle_delta_report import build_payload, render_markdown
from execute_phase33_controlled_review_actions import build_payload as execute_payload
from phase31_helpers import make_conn_with_candidate, phase31_candidate


class Phase33LifecycleDeltaReportTests(unittest.TestCase):
    def test_delta_report_shows_before_after(self):
        conn = make_conn_with_candidate(phase31_candidate("ev_plain", variable_type="capacity_signal"))
        execute_payload(conn, limit=1, execute=True)
        payload = build_payload(conn)
        self.assertGreater(payload["summary"]["audit_records"], 0)
        self.assertEqual(payload["summary"]["promotion_allowed_true_delta"], 0)
        self.assertIn("before_lifecycle_status", payload["rows"][0])
        self.assertIn("Phase 33 Evidence Lifecycle Delta Report", render_markdown(payload))


if __name__ == "__main__":
    unittest.main()
