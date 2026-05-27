import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_semantic_evidence_noise_filter import detect_noise


class Phase30SemanticEvidenceNoiseFilterTests(unittest.TestCase):
    def test_table_fragment_rejects(self):
        result = detect_noise({"quoted_span": "12%\n毛利\n114.", "payload": {"source_metadata": {"title": "业绩说明会附件PPT"}}})
        self.assertTrue(result["noise_detected"])
        self.assertIn("table_fragment", result["noise_types"])
        self.assertEqual(result["recommended_action"], "reject")

    def test_qa_answer_is_preserved(self):
        result = detect_noise({"quoted_span": "答：公司持续推进高速光模块产能建设，以满足客户需求增长。", "payload": {"source_metadata": {"section_type": "qa_section"}}})
        self.assertNotEqual(result["recommended_action"], "reject")

    def test_short_span_reviews_or_rejects(self):
        result = detect_noise({"quoted_span": "毛利"})
        self.assertIn(result["recommended_action"], {"review_required", "reject"})

    def test_ppt_slogan_rejects(self):
        result = detect_noise(
            {
                "quoted_span": "解放生产力 释放想象力\n用人工智能建设美好世界。",
                "payload": {"source_metadata": {"title": "科大讯飞业绩说明会附件PPT", "section_type": "product_structure"}},
            }
        )
        self.assertIn("ppt_title_only", result["noise_types"])
        self.assertEqual(result["recommended_action"], "reject")


if __name__ == "__main__":
    unittest.main()
