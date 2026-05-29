#!/usr/bin/env python3
import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parent.parent / "08_scripts" / "lib"
if str(L) not in sys.path: sys.path.insert(0, str(L))

class TestPhase64Dashboard(unittest.TestCase):
    def test_skip_network_dashboard(self):
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "08_scripts" / "reporting"))
        from build_phase64_connector_health_dashboard import build
        result = build("300308.SZ", skip_network=True)
        s = result.get("summary", result)
        self.assertEqual(s["ticker"], "300308.SZ")
        self.assertFalse(s["mock_used"])
        self.assertFalse(s["fixture_used"])
        self.assertFalse(s["raw_saved"])
        self.assertFalse(s["ocr_used"])
        self.assertEqual(s["pending_created"], 0)

    def test_dashboard_has_all_connectors(self):
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "08_scripts" / "reporting"))
        from build_phase64_connector_health_dashboard import build
        result = build("300308.SZ", skip_network=True)
        s = result.get("summary", result)
        for name in ["cninfo", "szse", "irm", "company_site"]:
            self.assertIn(name, s)

    def test_dashboard_best_path(self):
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "08_scripts" / "reporting"))
        from build_phase64_connector_health_dashboard import build
        result = build("300308.SZ", skip_network=True)
        s = result.get("summary", result)
        self.assertIn("best_available_path", s)

if __name__ == "__main__": unittest.main()
