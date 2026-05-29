import unittest,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(L) not in sys.path: sys.path.insert(0,str(L))
class TestIRReportBrief(unittest.TestCase):
    def test_build_returns_structure(self):
        try:
            from build_phase67_ir_report_evidence_brief import build
            r=build("300308.SZ")
            br=r.get("ir_report_evidence_brief",{})
            self.assertIn("company_name",br)
        except ImportError: self.skipTest("not importable")
    def test_no_trade_advice(self):
        try:
            from build_phase67_ir_report_evidence_brief import build, _md
            r=build("300308.SZ");md=_md(r)
            for f in ["买入","卖出","目标价","仓位","candidate","pending","validator","quality gate"]:
                self.assertNotIn(f,md,f"should not contain {f}")
        except ImportError: self.skipTest("not importable")
    def test_no_pending_order_trade(self):
        try:
            from build_phase67_ir_report_evidence_brief import build
            r=build("300308.SZ")
            self.assertEqual(r["ir_report_evidence_brief"]["pending_created"],0)
        except ImportError: self.skipTest("not importable")
if __name__=="__main__":unittest.main()
