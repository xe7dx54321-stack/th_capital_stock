import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_semantic_evidence_schema import make_semantic_extraction, validate_semantic_extraction


class Phase27SemanticEvidenceSchemaTests(unittest.TestCase):
    def test_quoted_span_required_and_must_come_from_chunk(self):
        item = make_semantic_extraction(
            ticker="300394.SZ",
            theme="ai_optical_interconnect",
            source_id="s1",
            chunk_id="c1",
            source_type="investor_relations_record",
            variable_type="capacity_signal",
            claim_text="产能建设",
            quoted_span="产能建设",
            evidence_strength="management_commentary",
            confidence="high",
        )
        issues = validate_semantic_extraction(item, chunk_text="公司推进产能建设。")
        self.assertFalse(any(issue["severity"] == "error" for issue in issues))
        self.assertEqual(item["confidence"], "medium")
        missing = dict(item, quoted_span="")
        self.assertTrue(any(issue["path"] == "quoted_span" for issue in validate_semantic_extraction(missing)))
        external = dict(item, quoted_span="NVIDIA")
        self.assertTrue(any(issue["message"] == "quoted_span must come from input chunk" for issue in validate_semantic_extraction(external, chunk_text="北美客户需求")))

    def test_unknown_variable_warns(self):
        item = make_semantic_extraction(
            ticker="300394.SZ",
            theme="ai_optical_interconnect",
            source_id="s1",
            chunk_id="c1",
            source_type="unknown",
            variable_type="bad",
            claim_text="x",
            quoted_span="x",
        )
        self.assertEqual(item["variable_type"], "unknown")
        self.assertTrue(any(issue["path"] == "variable_type" for issue in validate_semantic_extraction(item, chunk_text="x")))


if __name__ == "__main__":
    unittest.main()
