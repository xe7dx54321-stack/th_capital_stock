import unittest; from smr_chunk_quality_classifier import build_chunk_quality
class Phase51ChunkQualityTests(unittest.TestCase):
    def test_all_checked(self):
        chunks = [{"chunk_id":"ch_1","chunk_type":"qa_section","text_chars":85,"content":"产品占比持续提升"},
                  {"chunk_id":"ch_2","chunk_type":"unknown","text_chars":10,"content":"公告"},
                  {"chunk_id":"ch_3","chunk_type":"product_business_description","text_chars":51,"content":"光模块业务"}]
        r = build_chunk_quality(chunks)
        self.assertEqual(r["chunk_quality_report"]["chunks_checked"], 3)
    def test_too_short_not_allowed(self):
        chunks = [{"chunk_id":"ch_1","chunk_type":"qa_section","text_chars":5,"content":"short"}]
        r = build_chunk_quality(chunks)
        self.assertFalse(r["chunk_quality_report"]["rows"][0]["candidate_generation_allowed"])
    def test_high_signal_recognized(self):
        chunks = [{"chunk_id":"ch_1","chunk_type":"qa_section","text_chars":85,"content":"产品占比"}]
        r = build_chunk_quality(chunks)
        self.assertGreaterEqual(r["chunk_quality_report"]["high_signal_chunks"], 1)
if __name__ == "__main__": unittest.main()
