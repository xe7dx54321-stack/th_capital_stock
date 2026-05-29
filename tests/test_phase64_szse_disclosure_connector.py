#!/usr/bin/env python3
"""Tests for Phase 64 SZSE disclosure connector."""

import unittest, sys, json
from pathlib import Path
L = Path(__file__).resolve().parent.parent / "08_scripts" / "lib"
if str(L) not in sys.path: sys.path.insert(0, str(L))


class TestPhase64SZSEDisclosureConnector(unittest.TestCase):

    def test_dry_run_works(self):
        from smr_szse_disclosure_connector import fetch_szse_disclosure
        result = fetch_szse_disclosure("300308.SZ", max_sources=5, mode="dry-run", skip_network=False)
        inv = result["szse_disclosure_inventory"]
        self.assertEqual(inv["mode"], "dry-run")
        self.assertEqual(inv["status"], "dry_run")
        self.assertIn("would_attempt", inv)

    def test_skip_network_works(self):
        from smr_szse_disclosure_connector import fetch_szse_disclosure
        result = fetch_szse_disclosure("300308.SZ", skip_network=True)
        inv = result["szse_disclosure_inventory"]
        self.assertFalse(inv["network_attempted"])
        self.assertEqual(inv["status"], "skipped_network_disabled")

    def test_no_raw_no_ocr_no_mock(self):
        from smr_szse_disclosure_connector import fetch_szse_disclosure
        result = fetch_szse_disclosure("300308.SZ", skip_network=True)
        inv = result["szse_disclosure_inventory"]
        self.assertFalse(inv["raw_content_saved"])
        self.assertFalse(inv["ocr_used"])
        self.assertFalse(inv["mock_used"])
        self.assertFalse(inv["fixture_used"])

    def test_classify_szse_type(self):
        from smr_szse_disclosure_connector import _classify_szse_type
        self.assertEqual(_classify_szse_type({"title": "2024年度报告"}), "annual_report")
        self.assertEqual(_classify_szse_type({"title": "2024年第三季度报告"}), "quarterly_report")
        self.assertEqual(_classify_szse_type({"title": "投资者关系活动记录表"}), "investor_relations_record")
        self.assertEqual(_classify_szse_type({"title": "关于召开股东大会的通知"}), "announcement")


if __name__ == "__main__":
    unittest.main()
