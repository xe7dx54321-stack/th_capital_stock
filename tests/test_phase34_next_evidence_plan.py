import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase34_next_evidence_plan import build_payload
from phase34_helpers import make_phase34_conn


class Phase34NextEvidencePlanTests(unittest.TestCase):
    def test_next_evidence_plan_is_plan_only_and_uses_safe_sources(self):
        payload = build_payload(make_phase34_conn(), ticker="300394.SZ")
        self.assertGreater(payload["summary"]["evidence_plan_items"], 0)
        self.assertTrue(payload["safety"]["plan_only_no_evidence_written"])
        serialized = str(payload).lower()
        self.assertNotIn("bypass download", serialized)
        self.assertNotIn("force confirmed", serialized)


if __name__ == "__main__":
    unittest.main()
