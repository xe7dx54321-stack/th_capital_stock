import unittest,json,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path: sys.path.insert(0,str(R))
class TestBrief(unittest.TestCase):
    def test_no_trade_advice(self):
        try:
            from build_phase67b_ir_report_evidence_brief import build,_md
            r=build("300308.SZ");md=_md(r);md_low=md.lower()
            for f in ["买入","卖出","目标价","仓位","candidate","pending","validator"]:
                self.assertNotIn(f,md_low,f"should not contain {f}")
        except ImportError: self.skipTest("not importable")
    def test_no_pending_order_trade(self):
        try:
            from build_phase67b_ir_report_evidence_brief import build
            r=build("300308.SZ");br=r["phase67b_ir_report_evidence_brief"]
            self.assertEqual(br["pending_created"],0);self.assertEqual(br["paper_order_created"],0)
        except ImportError: self.skipTest("not importable")
if __name__=="__main__":unittest.main()
