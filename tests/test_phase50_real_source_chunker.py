import unittest; from phase50_helpers import make_phase50_conn; from build_phase50_real_source_chunks import build
class Phase50ChunkerTests(unittest.TestCase):
    def test_chunks_created(self): conn=make_phase50_conn(); p=build(conn,'300308.SZ'); c=p['real_source_chunks']; self.assertGreater(c['chunks_created'],0)
    def test_types_present(self): conn=make_phase50_conn(); p=build(conn,'300308.SZ'); self.assertIsInstance(p['real_source_chunks']['chunk_type_breakdown'],dict)
    def test_source_id(self): conn=make_phase50_conn(); p=build(conn,'300308.SZ'); rows=p['real_source_chunks']['rows']; self.assertTrue(all('source_id' in r for r in rows))
if __name__=='__main__': unittest.main()
