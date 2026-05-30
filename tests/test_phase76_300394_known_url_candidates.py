import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / "08_scripts" / "lib"
if str(L) not in sys.path: sys.path.insert(0, str(L))

class TestKnownURLCandidates(unittest.TestCase):
    def test_load_candidates(self):
        from smr_phase76_known_url_breakthrough import load_candidates
        cands = load_candidates("300394.SZ")
        self.assertGreater(len(cands), 0)
    def test_empty_url_invalid(self):
        from smr_phase76_known_url_breakthrough import validate_candidate
        r = validate_candidate({"url": "", "title": "test", "source_type": "known_pdf_url"})
        self.assertFalse(r["valid"])
    def test_empty_title_invalid(self):
        from smr_phase76_known_url_breakthrough import validate_candidate
        r = validate_candidate({"url": "https://example.com", "title": "", "source_type": "known_pdf_url"})
        self.assertFalse(r["valid"])
    def test_valid_source_type(self):
        from smr_phase76_known_url_breakthrough import validate_candidate
        r = validate_candidate({"url": "https://example.com", "title": "Test", "source_type": "known_pdf_url"})
        self.assertTrue(r["valid"])
    def test_invalid_source_type(self):
        from smr_phase76_known_url_breakthrough import validate_candidate
        r = validate_candidate({"url": "https://example.com", "title": "Test", "source_type": "invalid_type"})
        self.assertFalse(r["valid"])

if __name__ == "__main__": unittest.main()
