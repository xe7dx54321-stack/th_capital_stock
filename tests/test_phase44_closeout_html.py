import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "verification", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase44_closeout_html import SAFETY_BANNER, build_payload, render_html, write_html
from phase44_helpers import make_phase44_closeout_conn


class Phase44CloseoutHtmlTests(unittest.TestCase):
    def test_html_is_read_only(self):
        html = render_html(build_payload(make_phase44_closeout_conn()))
        self.assertIn("Phase 44 Manual Candidate Closeout", html)
        self.assertIn(SAFETY_BANNER, html)
        self.assertIn("phase45_final_research_packet_review", html)
        self.assertNotIn("target price", html.lower())

    def test_generated_html_path_is_ignored(self):
        self.assertIn("09_runbooks/generated/", (ROOT / ".gitignore").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "phase44_closeout.html"
            write_html(build_payload(make_phase44_closeout_conn()), output)
            self.assertTrue(output.exists())


if __name__ == "__main__":
    unittest.main()
