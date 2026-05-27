import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import smr_text_cache


class Phase29TextCacheTests(unittest.TestCase):
    def test_text_cache_write_read_and_gitignore(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = smr_text_cache.TEXT_CACHE_DIR
            smr_text_cache.TEXT_CACHE_DIR = Path(tmp) / "text_cache"
            try:
                meta = smr_text_cache.write_text_cache({"source_id": "s1", "ticker": "300394.SZ", "source_url": "https://x"}, "clean text " * 30)
                self.assertTrue(meta["text_hash"])
                self.assertIn("clean text", smr_text_cache.read_text_cache("s1", "https://x"))
                self.assertEqual(smr_text_cache.summarize_text_cache()["cache_entries"], 1)
            finally:
                smr_text_cache.TEXT_CACHE_DIR = original
        gitignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("08_data/generated/text_cache/**", gitignore)
        self.assertIn("*.text_cache.txt", gitignore)


if __name__ == "__main__":
    unittest.main()
