import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / "08_scripts" / "lib"
if str(L) not in sys.path: sys.path.insert(0, str(L))

class TestFallbackTextPool(unittest.TestCase):
    def test_build_empty(self):
        from smr_phase76_fallback_text_pool import build_text_pool
        r = build_text_pool([], [])
        pool = r["phase76_fallback_text_pool"]
        self.assertEqual(pool["texts_usable"], 0)
    def test_dedup(self):
        from smr_phase76_fallback_text_pool import build_text_pool
        t1 = [{"ticker": "X", "text_hash": "h1", "quality_grade": "good", "text_length": 100, "allowed_usage": "ctx"}]
        r = build_text_pool(t1, [{"ticker": "Y", "text_hash": "h1", "quality_grade": "good", "text_length": 100, "allowed_usage": "ctx"}])
        pool = r["phase76_fallback_text_pool"]
        self.assertEqual(pool["texts_usable"], 1)

if __name__ == "__main__": unittest.main()
