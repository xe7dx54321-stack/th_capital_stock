import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
TEST_DIR = ROOT / "tests"
for path in (LIB_DIR, REPORTING_DIR, TEST_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase32_evidence_review_html import SAFETY_BANNER, build_payload, render_html, write_html
from phase31_helpers import make_conn_with_candidate, phase31_candidate


class Phase32EvidenceReviewHtmlTests(unittest.TestCase):
    def test_html_summary_includes_safety_banner(self):
        conn = make_conn_with_candidate(phase31_candidate(variable_type="customer_allocation_signal", quality_bucket="weak_but_usable", quality_score=58))
        html = render_html(build_payload(conn, tickers="300394.SZ"))
        self.assertIn("Phase 32 Evidence Review Workbench", html)
        self.assertIn(SAFETY_BANNER, html)
        self.assertIn("--dry-run", html)

    def test_html_output_path_is_ignored(self):
        self.assertIn("09_runbooks/generated/", (ROOT / ".gitignore").read_text(encoding="utf-8"))
        conn = make_conn_with_candidate()
        payload = build_payload(conn, tickers="300394.SZ")
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "phase32_evidence_review.html"
            write_html(payload, output)
            self.assertTrue(output.exists())


if __name__ == "__main__":
    unittest.main()
