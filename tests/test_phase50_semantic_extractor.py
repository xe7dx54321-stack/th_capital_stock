import unittest; from phase50_helpers import make_phase50_conn; from build_phase50_semantic_extractions import build
class Phase50SemanticTests(unittest.TestCase):
    def test_extractions(self): conn=make_phase50_conn(); p=build(conn,'300308.SZ'); s=p['semantic_extractions']; self.assertGreater(s['semantic_extractions'],0)
    def test_quoted_span(self): conn=make_phase50_conn(); p=build(conn,'300308.SZ'); rows=p['semantic_extractions']['rows']; self.assertTrue(all('quoted_span' in r for r in rows))
if __name__=='__main__': unittest.main()
