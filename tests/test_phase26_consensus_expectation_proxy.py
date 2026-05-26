import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
REPORTING_DIR = ROOT / "08_scripts" / "reporting"
for path in (LIB_DIR, REPORTING_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase26_consensus_expectation_proxy import build_payload


class Phase26ConsensusExpectationProxyTests(unittest.TestCase):
    def test_internal_proxy_does_not_become_official_consensus(self):
        payload = build_payload(sqlite3.connect(":memory:"), ticker="300394.SZ")
        pack = payload["consensus_expectation_proxy"]
        self.assertFalse(pack["official_consensus_available"])
        self.assertEqual(pack["official_consensus_status"], "planned_only")
        self.assertFalse(pack["official_consensus_treated_as_internal"])
        self.assertIn("not official sell-side consensus", pack["limitations"])


if __name__ == "__main__":
    unittest.main()
