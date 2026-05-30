import unittest, sys
from pathlib import Path
L = Path(__file__).resolve().parents[1] / "08_scripts" / "lib"
if str(L) not in sys.path: sys.path.insert(0, str(L))

class TestPhase75FallbackTextConsolidator(unittest.TestCase):
    def test_empty_inputs(self):
        from smr_phase75_fallback_text_consolidator import consolidate
        r = consolidate()
        pool = r["phase75_fallback_text_pool"]
        self.assertEqual(pool["texts_usable"], 0)
    def test_dedup_same_hash(self):
        from smr_phase75_fallback_text_consolidator import consolidate
        r = consolidate(irm_result={"phase75_irm_html_real_execute": {"rows": [{"ticker": "X", "qa_text_usable": 1, "qa_items": [{"answer": "test", "qa_hash": "h1"}]}]}},
                        hygon_result={"phase75_hygon_ir_html_real_execute": {"ticker": "X", "rows": []}})
        pool = r["phase75_fallback_text_pool"]
        self.assertEqual(pool["texts_usable"], 1)
        r2 = consolidate(irm_result={"phase75_irm_html_real_execute": {"rows": [{"ticker": "X", "qa_text_usable": 1, "qa_items": [{"answer": "test", "qa_hash": "h1"}]}]}},
                         hygon_result={"phase75_hygon_ir_html_real_execute": {"ticker": "X", "rows": []}})
        pool2 = r2["phase75_fallback_text_pool"]
        self.assertEqual(pool2["texts_usable"], 1)
    def test_link_only_not_usable(self):
        from smr_phase75_fallback_text_consolidator import consolidate
        r = consolidate()
        pool = r["phase75_fallback_text_pool"]
        self.assertFalse(pool["mock_used"])

if __name__ == "__main__":
    unittest.main()
