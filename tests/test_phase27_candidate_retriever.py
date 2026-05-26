import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_ir_source_inventory import build_ir_source_inventory
from smr_semantic_candidate_retriever import retrieve_candidate_chunks
from smr_semantic_document_chunker import chunk_sources


class Phase27CandidateRetrieverTests(unittest.TestCase):
    def test_retriever_only_recalls_without_final_judgement(self):
        chunks = chunk_sources(build_ir_source_inventory("300394.SZ")["source_inventory"]["sources"])
        payload = retrieve_candidate_chunks(chunks)
        self.assertFalse(payload["no_candidate_chunks"])
        candidate = payload["candidate_chunks"][0]
        self.assertIsNone(candidate["final_variable_type"])
        self.assertIsNone(candidate["evidence_status"])
        self.assertTrue(payload["retriever_only"])


if __name__ == "__main__":
    unittest.main()
