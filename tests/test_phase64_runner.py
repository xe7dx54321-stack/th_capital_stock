#!/usr/bin/env python3
import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parent.parent / "08_scripts" / "lib"
if str(L) not in sys.path: sys.path.insert(0, str(L))

class TestPhase64Runner(unittest.TestCase):
    def test_runner_skip_network(self):
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "08_scripts" / "jobs"))
        from run_phase64_disclosure_connector_repair import run_phase64
        r = run_phase64("300308.SZ", 5, "execute", skip_network=True)
        p = r["phase64_disclosure_connector_repair"]
        self.assertEqual(p["mode"], "execute")
        self.assertFalse(p["mock_used"])
        self.assertFalse(p["fixture_used"])
        self.assertFalse(p["raw_saved"])
        self.assertFalse(p["ocr_used"])
        self.assertEqual(p["pending_created"], 0)
        self.assertEqual(p["paper_order_created"], 0)
        self.assertEqual(p["real_trade_created"], 0)

    def test_runner_dry_run(self):
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "08_scripts" / "jobs"))
        from run_phase64_disclosure_connector_repair import run_phase64
        r = run_phase64("300308.SZ", 5, "dry-run", skip_network=True)
        p = r["phase64_disclosure_connector_repair"]
        self.assertEqual(p["mode"], "dry-run")

    def test_runner_has_all_steps(self):
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "08_scripts" / "jobs"))
        from run_phase64_disclosure_connector_repair import run_phase64
        r = run_phase64("300308.SZ", 5, "execute", skip_network=True)
        p = r["phase64_disclosure_connector_repair"]
        step_names = [s["name"] for s in p["steps"]]
        expected = ["endpoint_registry", "cninfo_diagnostics", "szse_disclosure_connector",
                    "irm_qa_connector", "fallback_router", "connector_health_dashboard",
                    "small_controlled_fetch", "business_evidence_rerun"]
        for name in expected:
            self.assertIn(name, step_names)

    def test_runner_no_real_text_in_skip_network(self):
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "08_scripts" / "jobs"))
        from run_phase64_disclosure_connector_repair import run_phase64
        r = run_phase64("300308.SZ", 5, "execute", skip_network=True)
        p = r["phase64_disclosure_connector_repair"]
        self.assertFalse(p["real_text_used"])

if __name__ == "__main__": unittest.main()
