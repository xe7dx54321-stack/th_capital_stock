import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_ir_source_inventory import build_ir_source_inventory
from smr_semantic_document_chunker import chunk_sources


class Phase27SemanticDocumentChunkerTests(unittest.TestCase):
    def test_chunker_preserves_source_metadata_and_qa(self):
        sources = build_ir_source_inventory("300394.SZ")["source_inventory"]["sources"]
        chunks = chunk_sources(sources, max_chars=500)
        self.assertGreater(len(chunks), 0)
        self.assertTrue(all(chunk["source_id"] for chunk in chunks))
        self.assertTrue(all((chunk["metadata"] or {}).get("source_url") for chunk in chunks))
        self.assertTrue(any("问：" in chunk["text"] and "答：" in chunk["text"] for chunk in chunks))


if __name__ == "__main__":
    unittest.main()
