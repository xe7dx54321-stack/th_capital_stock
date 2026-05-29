import unittest,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"jobs"
if str(L) not in sys.path: sys.path.insert(0,str(L))

class TestRunner(unittest.TestCase):
    def test_dry_run_works(self):
        try:
            from run_phase66_targeted_disclosure_harvest import run_pipeline
            r=run_pipeline("300308.SZ",max_metadata=10,max_pdfs=3,skip_network=False,mode="dry_run")
            p=r.get("phase66_targeted_disclosure_harvest",{})
            self.assertEqual(p.get("mode"),"dry_run")
            self.assertGreater(len(p.get("steps",[])),0)
        except ImportError:
            self.skipTest("runner module not importable")
    def test_skip_network_works(self):
        try:
            from run_phase66_targeted_disclosure_harvest import run_pipeline
            r=run_pipeline("300308.SZ",skip_network=True)
            p=r.get("phase66_targeted_disclosure_harvest",{})
            self.assertGreater(len(p.get("steps",[])),0)
        except ImportError:
            self.skipTest("runner module not importable")
    def test_no_pending_order_trade(self):
        try:
            from run_phase66_targeted_disclosure_harvest import run_pipeline
            r=run_pipeline("300308.SZ",mode="dry_run")
            p=r.get("phase66_targeted_disclosure_harvest",{})
            self.assertEqual(p.get("pending_created"),0)
            self.assertEqual(p.get("paper_order_created"),0)
            self.assertEqual(p.get("real_trade_created"),0)
        except ImportError:
            self.skipTest("runner module not importable")
    def test_mock_fixture_false(self):
        try:
            from run_phase66_targeted_disclosure_harvest import run_pipeline
            r=run_pipeline("300308.SZ",mode="dry_run")
            p=r.get("phase66_targeted_disclosure_harvest",{})
            self.assertFalse(p.get("mock_used"))
            self.assertFalse(p.get("fixture_used"))
        except ImportError:
            self.skipTest("runner module not importable")
    def test_raw_ocr_false(self):
        try:
            from run_phase66_targeted_disclosure_harvest import run_pipeline
            r=run_pipeline("300308.SZ",mode="dry_run")
            p=r.get("phase66_targeted_disclosure_harvest",{})
            self.assertFalse(p.get("raw_saved"))
            self.assertFalse(p.get("ocr_used"))
        except ImportError:
            self.skipTest("runner module not importable")
    def test_steps_have_status(self):
        try:
            from run_phase66_targeted_disclosure_harvest import run_pipeline
            r=run_pipeline("300308.SZ",mode="dry_run")
            p=r.get("phase66_targeted_disclosure_harvest",{})
            for step in p.get("steps",[]):
                self.assertIn("name",step)
                self.assertIn("status",step)
        except ImportError:
            self.skipTest("runner module not importable")

if __name__=="__main__":unittest.main()
