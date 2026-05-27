import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_document_text_extraction import make_document_text_extraction


class Phase29DocumentTextExtractionSchemaTests(unittest.TestCase):
    def test_metadata_and_too_short_are_not_text_extracted(self):
        source = {"source_id": "s1", "ticker": "300394.SZ", "source_url": "https://x/a.pdf"}
        metadata = "证券代码：300394.SZ\n证券简称：天孚通信\n公告标题：投资者关系活动记录表\n公告日期：2026-05-01"
        result = make_document_text_extraction(source=source, document_type="pdf", extraction_status="text_extracted", text=metadata)
        self.assertEqual(result["extraction_status"], "metadata_only")
        short = make_document_text_extraction(source=source, document_type="pdf", extraction_status="text_extracted", text="产能")
        self.assertEqual(short["extraction_status"], "text_too_short")
        self.assertFalse(result["raw_content_saved"])


if __name__ == "__main__":
    unittest.main()
