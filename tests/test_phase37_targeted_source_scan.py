import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "jobs", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from run_phase37_targeted_source_scan import build_payload
from phase37_helpers import make_phase37_conn


class Phase37TargetedSourceScanTests(unittest.TestCase):
    def test_source_scan_uses_existing_body_chunks_without_writes(self):
        payload = build_payload(make_phase37_conn(), ticker="300308.SZ", dry_run=True)
        body = payload["targeted_source_scan"]
        self.assertGreater(body["candidate_chunks_found"], 0)
        for result in body["scan_results"]:
            for chunk in result.get("candidate_chunks") or []:
                self.assertIn(chunk["quoted_span"], chunk["chunk_text"])
                self.assertTrue(chunk["source_url"])
        self.assertFalse(payload["safety"]["metadata_fabricated_as_body"])
        self.assertFalse(payload["safety"]["dry_run_wrote_db"])


if __name__ == "__main__":
    unittest.main()
