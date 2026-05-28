import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "verification", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from phase34_helpers import make_phase34_conn
from validate_phase34_valuation_support_post_governance import build_payload


class Phase34ValuationSupportPostGovernanceTests(unittest.TestCase):
    def test_semantic_evidence_does_not_replace_valuation_gate(self):
        payload = build_payload(make_phase34_conn(), ticker="300394.SZ")
        self.assertEqual(payload["summary"]["valuation_gate_promoted"], 0)
        self.assertFalse(payload["safety"]["semantic_evidence_replaces_valuation"])
        self.assertEqual(payload["summary"]["new_pending_created"], 0)


if __name__ == "__main__":
    unittest.main()
