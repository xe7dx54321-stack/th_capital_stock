import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / "08_scripts" / "lib"
J = Path(__file__).resolve().parents[1] / "08_scripts" / "jobs"
for p in [str(L), str(J)]: 
    if p not in sys.path: sys.path.insert(0, p)
class Test300394RealExecute(unittest.TestCase):
    def test_dry_run(self):
        from run_phase70_300394_real_execute import run
        r = run(mode="dry_run"); d = r["phase70_300394_real_execute"]
        self.assertEqual(d["overall_status"], "dry_run")
    def test_blocked_has_blocker_if_no_identity(self):
        from run_phase70_300394_real_execute import run
        r = run(mode="execute"); d = r["phase70_300394_real_execute"]
        if not d.get("identity_found"):
            self.assertIn("blocker", d)
    def test_no_mock_fixture(self):
        from run_phase70_300394_real_execute import run
        r = run(mode="execute"); d = r["phase70_300394_real_execute"]
        self.assertFalse(d.get("mock_used",True)); self.assertFalse(d.get("fixture_used",True))
    def test_pending_order_trade_zero(self):
        from run_phase70_300394_real_execute import run
        r = run(mode="execute"); d = r["phase70_300394_real_execute"]
        self.assertEqual(d.get("pending_created",-1),0)
        self.assertEqual(d.get("paper_order_created",-1),0)
        self.assertEqual(d.get("real_trade_created",-1),0)
    def test_no_raw_no_ocr(self):
        from run_phase70_300394_real_execute import run
        r = run(mode="execute"); d = r["phase70_300394_real_execute"]
        self.assertFalse(d.get("raw_saved",True) if "raw_saved" in d else False or True)
        self.assertFalse(d.get("ocr_used",True) if "ocr_used" in d else False or True)
if __name__ == "__main__": unittest.main()
