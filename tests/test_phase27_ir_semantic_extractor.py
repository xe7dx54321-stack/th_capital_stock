import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
JOBS_DIR = ROOT / "08_scripts" / "jobs"
for path in (LIB_DIR, JOBS_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_semantic_ir_evidence import build_payload
from smr_ir_semantic_extractor import PROMPT_GUARDRAILS


class Phase27IRSemanticExtractorTests(unittest.TestCase):
    def test_mock_extractor_stable_and_llm_default_disabled(self):
        payload = build_payload(tickers="300394.SZ", mode="mock")
        self.assertGreater(payload["summary"]["semantic_extractions"], 0)
        self.assertFalse(payload["rows"][0]["llm_enabled"])
        self.assertIn("Do not rewrite \"North American customer\" as NVIDIA", PROMPT_GUARDRAILS)
        text = str(payload["rows"][0]["semantic_extractions"])
        self.assertNotIn("'NVIDIA'", text)


if __name__ == "__main__":
    unittest.main()
