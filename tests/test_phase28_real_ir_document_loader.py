import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_real_ir_document_loader import attach_real_text_to_source, load_real_ir_document_text
from smr_semantic_document_chunker import chunk_document


class Phase28RealIRDocumentLoaderTests(unittest.TestCase):
    def test_no_text_reports_unavailable_and_chunk_keeps_metadata(self):
        missing = load_real_ir_document_text({"source_id": "s1", "ticker": "300394.SZ", "metadata": {}})
        self.assertTrue(missing["text_unavailable"])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "source.md"
            path.write_text("# Source\n\n## Extracted Text\n\n问：产能？\n答：公司推进高速光器件产能建设。", encoding="utf-8")
            source = {
                "source_id": "s2",
                "ticker": "300394.SZ",
                "source_type": "investor_relations_record",
                "title": "投资者关系活动记录表",
                "published_at": "2026-05-01",
                "source_url": "https://static.cninfo.com.cn/a.pdf",
                "real_source": True,
                "metadata": {"parsed_text_path": str(path)},
            }
            enriched = attach_real_text_to_source(source)
            chunks = chunk_document(enriched)
            self.assertFalse(enriched["text_unavailable"])
            self.assertTrue(chunks)
            self.assertTrue(chunks[0]["metadata"]["real_source"])
            self.assertEqual(chunks[0]["metadata"]["source_url"], source["source_url"])


if __name__ == "__main__":
    unittest.main()
