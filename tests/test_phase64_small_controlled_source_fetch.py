#!/usr/bin/env python3
import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parent.parent / "08_scripts" / "lib"
if str(L) not in sys.path: sys.path.insert(0, str(L))

class TestPhase64SmallControlledSourceFetch(unittest.TestCase):
    def test_dry_run(self):
        from smr_small_controlled_source_fetch import run_small_controlled_source_fetch
        r = run_small_controlled_source_fetch("300308.SZ", 5, "dry-run", skip_network=False)
        f = r["small_controlled_source_fetch"]
        self.assertEqual(f["status"], "dry_run")

    def test_skip_network(self):
        from smr_small_controlled_source_fetch import run_small_controlled_source_fetch
        r = run_small_controlled_source_fetch("300308.SZ", 5, "execute", skip_network=True)
        f = r["small_controlled_source_fetch"]
        self.assertFalse(f["network_attempted"])

    def test_no_mock_no_fixture_no_raw_no_ocr(self):
        from smr_small_controlled_source_fetch import run_small_controlled_source_fetch
        r = run_small_controlled_source_fetch("300308.SZ", 5, "execute", skip_network=True)
        f = r["small_controlled_source_fetch"]
        self.assertFalse(f["mock_used"])
        self.assertFalse(f["fixture_used"])
        self.assertFalse(f["raw_saved"])
        self.assertFalse(f["ocr_used"])

    def test_selected_sources_present(self):
        from smr_small_controlled_source_fetch import run_small_controlled_source_fetch
        r = run_small_controlled_source_fetch("300308.SZ", 5, "execute", skip_network=True)
        f = r["small_controlled_source_fetch"]
        self.assertIn("selected_sources", f)

if __name__ == "__main__": unittest.main()
