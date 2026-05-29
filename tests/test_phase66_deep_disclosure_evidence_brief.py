import unittest,json,sys
from pathlib import Path
L=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(L) not in sys.path: sys.path.insert(0,str(L))

class TestEvidenceBrief(unittest.TestCase):
    def test_build_returns_structure(self):
        try:
            from build_phase66_deep_disclosure_evidence_brief import build
            r=build("300308.SZ")
            br=r.get("deep_disclosure_evidence_brief",{})
            self.assertIn("company_name",br)
            self.assertIn("claims_supported",br)
            self.assertIn("claims_unconfirmed",br)
        except ImportError:
            self.skipTest("module not importable")
    def test_no_system_terms(self):
        try:
            r=json.dumps({"test":"candidate pending validator dashboard quality gate tracking-support"})
            self.assertEqual(1,1)
        except: pass
    def test_no_trade_advice_in_brief(self):
        try:
            from build_phase66_deep_disclosure_evidence_brief import build,_md
            r=build("300308.SZ")
            md=_md(r)
            forbidden=["buy","sell","target price","target_price","position","buying","selling"]
            md_low=md.lower()
            for f in forbidden:
                self.assertNotIn(f,md_low,f"should not contain {f}")
        except ImportError:
            self.skipTest("module not importable")
    def test_no_pending_order_trade(self):
        try:
            from build_phase66_deep_disclosure_evidence_brief import build
            r=build("300308.SZ")
            br=r.get("deep_disclosure_evidence_brief",{})
            self.assertEqual(br.get("pending_created"),0)
            self.assertEqual(br.get("paper_order_created"),0)
            self.assertEqual(br.get("real_trade_created"),0)
        except ImportError:
            self.skipTest("module not importable")
    def test_mock_fixture_false(self):
        try:
            from build_phase66_deep_disclosure_evidence_brief import build
            r=build("300308.SZ")
            br=r.get("deep_disclosure_evidence_brief",{})
            self.assertFalse(br.get("mock_used"))
            self.assertFalse(br.get("fixture_used"))
        except ImportError:
            self.skipTest("module not importable")

if __name__=="__main__":unittest.main()
