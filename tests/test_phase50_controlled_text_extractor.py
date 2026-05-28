import unittest; from phase50_helpers import make_phase50_conn; from run_phase50_controlled_text_extraction import build_extraction_result; from smr_real_source_monitor_schema import get_sample_sources
class Phase50TextExtractorTests(unittest.TestCase):
    def test_dry_run(self): conn=make_phase50_conn(); sources=get_sample_sources('300308.SZ'); p=build_extraction_result(sources,'300308.SZ',mode='dry-run'); r=p['controlled_text_extraction']; self.assertGreater(r['text_extracted'],0)
    def test_no_raw_saved(self): conn=make_phase50_conn(); sources=get_sample_sources('300308.SZ'); p=build_extraction_result(sources,'300308.SZ',mode='dry-run'); self.assertFalse(p['controlled_text_extraction']['raw_content_saved'])
    def test_safety(self): conn=make_phase50_conn(); sources=get_sample_sources('300308.SZ'); p=build_extraction_result(sources,'300308.SZ',mode='dry-run'); self.assertTrue(p['safety']['no_raw_saved'])
if __name__=='__main__': unittest.main()
