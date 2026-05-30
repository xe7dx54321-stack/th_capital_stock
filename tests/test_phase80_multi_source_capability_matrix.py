import unittest,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1]/"08_scripts"/"reporting"
if str(R) not in sys.path:sys.path.insert(0,str(R))
class TestMatrix(unittest.TestCase):
    def test_build(self):from build_phase80_multi_source_capability_matrix import build;r=build();m=r["phase80_multi_source_capability_matrix"];self.assertGreater(m["tickers_checked"],0)
    def test_has_rows(self):from build_phase80_multi_source_capability_matrix import build;r=build();rows=r["phase80_multi_source_capability_matrix"]["rows"];self.assertGreaterEqual(len(rows),3)
    def test_300308_ok(self):from build_phase80_multi_source_capability_matrix import build;r=build();rows=r["phase80_multi_source_capability_matrix"]["rows"];row=[x for x in rows if x["ticker"]=="300308.SZ"];self.assertEqual(len(row),1);self.assertIn("full_chain",row[0]["overall"])
    def test_688041_has_consistency(self):from build_phase80_multi_source_capability_matrix import build;r=build();rows=r["phase80_multi_source_capability_matrix"]["rows"];row=[x for x in rows if x["ticker"]=="688041.SH"];self.assertEqual(len(row),1);self.assertIn("consistent",row[0]["overall"])
    def test_300394_blocker(self):from build_phase80_multi_source_capability_matrix import build;r=build();rows=r["phase80_multi_source_capability_matrix"]["rows"];row=[x for x in rows if x["ticker"]=="300394.SZ"];self.assertEqual(len(row),1);self.assertIn("blocked",row[0]["overall"])
    def test_no_pending(self):from build_phase80_multi_source_capability_matrix import build;r=build();m=r["phase80_multi_source_capability_matrix"];self.assertEqual(m["pending_created"],0);self.assertEqual(m["paper_order_created"],0);self.assertEqual(m["real_trade_created"],0)
if __name__=="__main__":unittest.main()
