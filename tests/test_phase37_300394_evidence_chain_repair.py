import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "jobs", ROOT / "08_scripts" / "verification", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from run_phase37_300394_evidence_chain_repair import build_payload as build_repair
from validate_phase37_300394_evidence_chain_repair import build_payload as validate_repair


class Phase37300394EvidenceChainRepairTests(unittest.TestCase):
    def test_repair_dry_run_reports_root_cause_without_fake_evidence(self):
        payload = build_repair(sqlite3.connect(":memory:"), mode="dry_run")
        body = payload["evidence_chain_repair"]
        self.assertEqual(body["repair_status"], "partial_repair_dry_run")
        self.assertTrue(body["root_cause"])
        self.assertEqual(body["candidates_written"], 0)
        self.assertFalse(payload["safety"]["fake_evidence_written"])
        validation = validate_repair(sqlite3.connect(":memory:"))
        self.assertEqual(validation["validation"]["overall_status"], "pass")


if __name__ == "__main__":
    unittest.main()
