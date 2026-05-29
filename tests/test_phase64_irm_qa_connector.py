#!/usr/bin/env python3
import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parent.parent / "08_scripts" / "lib"
if str(L) not in sys.path: sys.path.insert(0, str(L))

class TestPhase64IRMQAConnector(unittest.TestCase):
    def test_dry_run(self):
        from smr_irm_interactive_qa_connector import fetch_irm_qa
        r = fetch_irm_qa("300308.SZ", max_sources=5, mode="dry-run", skip_network=False)
        inv = r["irm_qa_inventory"]
        self.assertEqual(inv["status"], "dry_run")
        self.assertIn("would_attempt", inv)

    def test_skip_network(self):
        from smr_irm_interactive_qa_connector import fetch_irm_qa
        r = fetch_irm_qa("300308.SZ", skip_network=True)
        inv = r["irm_qa_inventory"]
        self.assertFalse(inv["network_attempted"])

    def test_no_raw_no_ocr_no_mock(self):
        from smr_irm_interactive_qa_connector import fetch_irm_qa
        r = fetch_irm_qa("300308.SZ", skip_network=True)
        inv = r["irm_qa_inventory"]
        self.assertFalse(inv["raw_content_saved"])
        self.assertFalse(inv["ocr_used"])
        self.assertFalse(inv["mock_used"])

    def test_clean_html(self):
        from smr_irm_interactive_qa_connector import _clean_html
        self.assertEqual(_clean_html("<div>hello</div>"), "hello")
        self.assertEqual(_clean_html("<p>text &amp; more</p>"), "text more")
        self.assertEqual(_clean_html(""), "")

    def test_parse_qa_from_html_empty(self):
        from smr_irm_interactive_qa_connector import _parse_qa_from_html
        result = _parse_qa_from_html("")
        self.assertEqual(result, [])

    def test_html_not_json(self):
        from smr_irm_interactive_qa_connector import fetch_irm_qa
        r = fetch_irm_qa("300308.SZ", skip_network=True)
        inv = r["irm_qa_inventory"]
        self.assertFalse(inv["api_json_available"])

if __name__ == "__main__": unittest.main()
