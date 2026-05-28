import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase41_followup_html import SAFETY_BANNER, build_payload, render_html, write_html
from phase41_helpers import make_phase41_conn_with_followups


class Phase41FollowupHtmlTests(unittest.TestCase):
    def test_html_is_read_only_and_has_followup_queue(self):
        html = render_html(build_payload(make_phase41_conn_with_followups()))
        self.assertIn("Phase 41 Research Follow-up Queue", html)
        self.assertIn(SAFETY_BANNER, html)
        self.assertIn("--dry-run", html)
        self.assertNotIn("target price", html.lower())

    def test_generated_html_path_is_ignored(self):
        self.assertIn("09_runbooks/generated/", (ROOT / ".gitignore").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "phase41_followup.html"
            write_html(build_payload(make_phase41_conn_with_followups()), output)
            self.assertTrue(output.exists())


if __name__ == "__main__":
    unittest.main()
