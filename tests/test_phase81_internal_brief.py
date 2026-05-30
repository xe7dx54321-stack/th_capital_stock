import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestInternalBrief(unittest.TestCase):
    def test_build(self):from build_phase81_internal_brief import build;r=build();b=r["phase81_internal_brief"];self.assertGreater(b["sections"],0);self.assertGreaterEqual(b["tickers_covered"],1)
    def test_has_markdown(self):from build_phase81_internal_brief import build;r=build();self.assertIn("markdown",r["phase81_internal_brief"])
    def test_no_buy_sell(self):from build_phase81_internal_brief import build;r=build();md=r["phase81_internal_brief"]["markdown"];self.assertNotIn("buy",md.lower().split());self.assertNotIn("sell",md.lower().split())
    def test_no_target_price(self):from build_phase81_internal_brief import build;r=build();md=r["phase81_internal_brief"]["markdown"];self.assertNotIn("target price",md.lower());self.assertNotIn("target_price",md.lower())
    def test_no_pending(self):from build_phase81_internal_brief import build;r=build();md=r["phase81_internal_brief"]["markdown"];self.assertNotIn("pending",md.lower())
if __name__=="__main__":unittest.main()
