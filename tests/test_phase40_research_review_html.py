import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase40_research_review_html import SAFETY_BANNER, build_payload, render_html, write_html
from phase39_helpers import make_phase39_conn


class Phase40ResearchReviewHtmlTests(unittest.TestCase):
    def test_html_is_read_only_and_has_dry_run_commands(self):
        payload = build_payload(make_phase39_conn())
        html = render_html(payload)
        self.assertIn("Phase 40 Research Review Workbench", html)
        self.assertIn(SAFETY_BANNER, html)
        self.assertIn("--dry-run", html)
        self.assertIn("300394 Repair Status", html)
        self.assertNotIn("target price", html.lower())
        self.assertNotIn("\"buy\"", json.dumps(payload).lower())

    def test_html_output_path_is_ignored(self):
        self.assertIn("09_runbooks/generated/", (ROOT / ".gitignore").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "phase40_research_review.html"
            write_html(build_payload(make_phase39_conn()), output)
            self.assertTrue(output.exists())


if __name__ == "__main__":
    unittest.main()
