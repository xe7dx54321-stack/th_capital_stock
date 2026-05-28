import unittest; from phase50_helpers import make_phase50_conn; from build_phase50_text_normalization_report import build
class Phase50NormalizerTests(unittest.TestCase):
    def test_normalized(self): conn=make_phase50_conn(); p=build(conn,'300308.SZ'); r=p['text_normalization_report']; self.assertGreater(r['texts_checked'],0)
    def test_preserves_source(self): conn=make_phase50_conn(); p=build(conn,'300308.SZ'); rows=p['text_normalization_report']['rows']; self.assertTrue(all('source_id' in r for r in rows))
    def test_too_short_count(self): conn=make_phase50_conn(); p=build(conn,'300308.SZ'); self.assertIsInstance(p['text_normalization_report']['too_short'],int)
if __name__=='__main__': unittest.main()
