import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_semantic_document_chunker import chunk_document
from smr_semantic_candidate_retriever import retrieve_candidate_chunks


class Phase30TablePptQualityGateTests(unittest.TestCase):
    def test_table_fragment_chunk_filtered_from_retrieval(self):
        chunks = chunk_document(
            {
                "source_id": "s1",
                "ticker": "002230.SZ",
                "source_type": "investor_relations_record",
                "title": "业绩说明会附件PPT",
                "source_url": "https://x",
                "text": "12%\n毛利\n114.",
                "real_source": True,
            }
        )
        self.assertTrue(chunks)
        self.assertEqual(chunks[0]["metadata"]["chunk_noise_action"], "reject")
        self.assertEqual(retrieve_candidate_chunks(chunks)["candidate_chunks"], [])

    def test_qa_chunk_preserved(self):
        chunks = chunk_document(
            {
                "source_id": "s1",
                "ticker": "300308.SZ",
                "source_type": "investor_relations_record",
                "title": "投资者关系活动记录表",
                "source_url": "https://x",
                "text": "问：产能情况如何？\n答：公司持续推进高速光模块产能建设，以满足客户需求增长。",
                "real_source": True,
            }
        )
        self.assertTrue(chunks)
        self.assertNotEqual(chunks[0]["metadata"]["chunk_noise_action"], "reject")


if __name__ == "__main__":
    unittest.main()
