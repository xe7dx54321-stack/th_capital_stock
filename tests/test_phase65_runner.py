#!/usr/bin/env python3
import unittest,sys
from pathlib import Path
L=Path(__file__).resolve().parent.parent/"08_scripts"/"lib"
if str(L) not in sys.path: sys.path.insert(0,str(L))
class TestPhase65Runner(unittest.TestCase):
    def test_runner_skip_network(self):
        sys.path.insert(0,str(Path(__file__).resolve().parent.parent/"08_scripts"/"jobs"))
        from run_phase65_disclosure_endpoint_breakthrough import run_phase65
        r=run_phase65("300308.SZ","execute",skip_network=True)
        p=r["phase65_disclosure_endpoint_breakthrough"]
        self.assertEqual(p["mode"],"execute")
        self.assertFalse(p["mock_used"])
        self.assertFalse(p["fixture_used"])
        self.assertFalse(p["raw_saved"])
        self.assertFalse(p["ocr_used"])
        self.assertEqual(p["pending_created"],0)
        self.assertEqual(p["paper_order_created"],0)
        self.assertEqual(p["real_trade_created"],0)
    def test_runner_dry_run(self):
        sys.path.insert(0,str(Path(__file__).resolve().parent.parent/"08_scripts"/"jobs"))
        from run_phase65_disclosure_endpoint_breakthrough import run_phase65
        r=run_phase65("300308.SZ","dry-run",skip_network=True)
        p=r["phase65_disclosure_endpoint_breakthrough"]
        self.assertEqual(p["mode"],"dry-run")
    def test_runner_has_all_steps(self):
        sys.path.insert(0,str(Path(__file__).resolve().parent.parent/"08_scripts"/"jobs"))
        from run_phase65_disclosure_endpoint_breakthrough import run_phase65
        r=run_phase65("300308.SZ","execute",skip_network=True)
        p=r["phase65_disclosure_endpoint_breakthrough"]
        names=[s["name"] for s in p["steps"]]
        for n in ["cninfo_stock_identity_resolver","cninfo_announcement_query_matrix","cninfo_metadata_connector_patch","cninfo_pdf_url_extractor","cninfo_pdf_text_validation","szse_endpoint_explorer","metadata_breakthrough_dashboard","business_evidence_rerun"]:
            self.assertIn(n,names)
if __name__=="__main__":unittest.main()
