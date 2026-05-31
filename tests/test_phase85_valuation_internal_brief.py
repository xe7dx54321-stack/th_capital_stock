import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestInternalBrief(unittest.TestCase):
    def test_build(self):from build_phase85_valuation_internal_brief import build;r=build();b=r["phase85_valuation_internal_brief"];self.assertGreater(b["sections"],0)
    def test_has_markdown(self):from build_phase85_valuation_internal_brief import build;r=build();b=r["phase85_valuation_internal_brief"];self.assertIn("markdown",b)
    def test_no_system_terms(self):from build_phase85_valuation_internal_brief import build;r=build();md=r["phase85_valuation_internal_brief"]["markdown"];self.assertNotIn("pipeline",md.lower());self.assertNotIn("buy",md.lower().split("not")[-1][:50] if "not" in md.lower() else "");self.assertNotIn("sell",md.lower().split("not")[-1][:50] if "not" in md.lower() else "")
if __name__=="__main__":unittest.main()
