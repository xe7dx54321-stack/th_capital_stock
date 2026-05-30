import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
L=Path(__file__).resolve().parents[1]/"08_scripts"/"lib"
if str(R) not in sys.path:sys.path.insert(0,str(R))
if str(L) not in sys.path:sys.path.insert(0,str(L))
class TestLint(unittest.TestCase):
    def test_build(self):
        from build_phase77_brief_quality_lint import build
        r=build();lt=r["phase77_brief_quality_lint"]
        self.assertIn(lt["overall_status"],["pass","fail"])
    def test_no_trade(self):
        from build_phase77_brief_quality_lint import build
        r=build();lt=r["phase77_brief_quality_lint"]
        self.assertEqual(lt["trade_advice_terms_found"],0)
if __name__=="__main__":unittest.main()
