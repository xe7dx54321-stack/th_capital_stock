import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import smr_text_cache
from smr_real_ir_document_loader import attach_real_text_to_source
from smr_semantic_document_chunker import chunk_document


class Phase29ChunkerTextCacheIntegrationTests(unittest.TestCase):
    def test_metadata_only_skipped_and_cache_chunks_keep_metadata(self):
        source = {"source_id": "s1", "ticker": "300394.SZ", "source_url": "https://x/a.pdf", "published_at": "2026-05-01", "text_snippet": "证券代码：300394.SZ\n证券简称：天孚通信\n公告标题：投资者关系活动记录表", "real_source": True}
        skipped = attach_real_text_to_source(source, skip_metadata_only=True)
        self.assertTrue(skipped["text_unavailable"])
        with tempfile.TemporaryDirectory() as tmp:
            original = smr_text_cache.TEXT_CACHE_DIR
            smr_text_cache.TEXT_CACHE_DIR = Path(tmp) / "text_cache"
            try:
                smr_text_cache.write_text_cache(source, "问：产能如何？\n答：公司推进高速光器件产能建设，以满足客户需求增长。" * 8)
                enriched = attach_real_text_to_source(source, use_text_cache=True)
                chunks = chunk_document(enriched)
                self.assertTrue(chunks)
                self.assertEqual(chunks[0]["metadata"]["source_url"], source["source_url"])
                self.assertEqual(chunks[0]["metadata"]["published_at"], source["published_at"])
            finally:
                smr_text_cache.TEXT_CACHE_DIR = original


if __name__ == "__main__":
    unittest.main()
