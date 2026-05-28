import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "jobs", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase37_targeted_evidence_candidates import build_payload
from phase37_helpers import make_phase37_conn


class Phase37TargetedEvidenceCandidateBuilderTests(unittest.TestCase):
    def test_candidate_builder_uses_quality_guard_without_promotion(self):
        payload = build_payload(make_phase37_conn(), ticker="300308.SZ", mode="dry_run")
        body = payload["targeted_evidence_candidates"]
        self.assertGreater(body["candidates_created"], 0)
        self.assertGreater(body["eligible_for_persistence"], 0)
        self.assertEqual(body["candidates_written"], 0)
        self.assertFalse(body["dry_run_wrote_db"])
        self.assertEqual(body["usable_for_promotion_true"], 0)
        self.assertTrue(payload["safety"]["phase30_guard_used"])
        self.assertFalse(payload["safety"]["sensitive_variable_confirmed"])


if __name__ == "__main__":
    unittest.main()
