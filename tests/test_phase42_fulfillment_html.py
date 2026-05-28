import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "verification", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase42_fulfillment_html import SAFETY_BANNER, build_payload, render_html, write_html
from phase42_helpers import make_phase42_conn


class Phase42FulfillmentHtmlTests(unittest.TestCase):
    def test_html_is_read_only(self):
        html = render_html(build_payload(make_phase42_conn()))
        self.assertIn("Phase 42 Follow-up Fulfillment", html)
        self.assertIn(SAFETY_BANNER, html)
        self.assertIn("Pending allowed: False", html)
        self.assertNotIn("target price", html.lower())

    def test_generated_html_path_is_ignored(self):
        self.assertIn("09_runbooks/generated/", (ROOT / ".gitignore").read_text(encoding="utf-8"))
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "phase42_fulfillment.html"
            write_html(build_payload(make_phase42_conn()), output)
            self.assertTrue(output.exists())


if __name__ == "__main__":
    unittest.main()
