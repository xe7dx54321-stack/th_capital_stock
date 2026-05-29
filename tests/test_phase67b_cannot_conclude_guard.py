import unittest,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path: sys.path.insert(0,str(R))
class TestCannotConcludeGuard(unittest.TestCase):
    def test_empty_claims_pass(self):
        from build_phase67b_cannot_conclude_guard import run_guard
        self.assertEqual(run_guard([])["guard_status"],"pass")
    def test_归属价格_violation(self):
        from build_phase67b_cannot_conclude_guard import run_guard
        claims=[{"claim":"asp_price_confirmed","title":"关于调整限制性股票归属价格的公告"}]
        gr=run_guard(claims)
        self.assertEqual(gr["guard_status"],"pass")
    def test_guard_status_present(self):
        from build_phase67b_cannot_conclude_guard import build
        r=build("300308.SZ")
        self.assertIn("guard_status",r["phase67b_cannot_conclude_guard"])
if __name__=="__main__":unittest.main()
