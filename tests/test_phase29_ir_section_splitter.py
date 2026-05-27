import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_ir_section_splitter import split_ir_sections


class Phase29IRSectionSplitterTests(unittest.TestCase):
    def test_qa_structure_is_preserved_and_prioritized(self):
        source = {"source_id": "s1", "title": "投资者关系活动主要内容介绍", "text": "问：产能如何？\n答：公司推进产能建设。\n\n问：客户如何？\n答：未披露具体客户 allocation。"}
        payload = split_ir_sections(source)
        self.assertTrue(payload["sections"])
        self.assertEqual(payload["sections"][0]["section_type"], "qa_section")
        self.assertEqual(payload["sections"][0]["priority"], "high")


if __name__ == "__main__":
    unittest.main()
