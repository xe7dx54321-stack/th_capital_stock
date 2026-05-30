import unittest, sys
from pathlib import Path
R = Path(__file__).resolve().parents[1] / "08_scripts" / "reporting"
if str(R) not in sys.path: sys.path.insert(0, str(R))
class TestInternalBrief(unittest.TestCase):
    def test_has_structure(self):
        from build_phase71_internal_brief import build
        r = build(); md = r["phase71_internal_brief"]["markdown"]
        self.assertIn("老板摘要", md); self.assertIn("研究员详情", md)
    def test_no_system_terms(self):
        from build_phase71_internal_brief import build
        r = build(); md = r["phase71_internal_brief"]["markdown"]
        for term in ["candidate","pending","dashboard","validator","runner","mock","fixture","quality gate","pipeline"]:
            self.assertNotIn(term, md.lower())
    def test_no_teaching(self):
        from build_phase71_internal_brief import build
        r = build(); md = r["phase71_internal_brief"]["markdown"]
        for term in ["建议关注","值得关注","有望受益","未来可期","下一步重点看"]:
            self.assertNotIn(term, md)
    def test_no_trade_advice(self):
        from build_phase71_internal_brief import build
        r = build(); md = r["phase71_internal_brief"]["markdown"]
        for term in ["买入","卖出","目标价","仓位","加仓","减仓"]:
            self.assertNotIn(term, md)
    def test_covers_three_tickers(self):
        from build_phase71_internal_brief import build
        r = build(); br = r["phase71_internal_brief"]
        self.assertGreaterEqual(br.get("tickers_covered", 0), 2)
if __name__ == "__main__": unittest.main()
