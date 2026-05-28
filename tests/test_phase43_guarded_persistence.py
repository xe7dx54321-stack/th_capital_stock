import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "jobs", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from persist_phase43_manual_intake_candidates import build_payload
from phase42_helpers import make_phase42_conn
from phase43_helpers import make_phase43_conn_with_candidates
from smr_manual_intake_candidate_generator import list_manual_intake_candidates


class Phase43GuardedPersistenceTests(unittest.TestCase):
    def test_dry_run_does_not_write_and_execute_marks_persisted(self):
        dry = build_payload(make_phase42_conn(), ticker="300308.SZ", mode="dry_run")
        dry_body = dry["manual_intake_persistence"]
        self.assertEqual(dry_body["candidates_available"], 3)
        self.assertEqual(dry_body["candidates_written"], 0)

        conn = make_phase43_conn_with_candidates()
        executed = build_payload(conn, ticker="300308.SZ", mode="execute")
        body = executed["manual_intake_persistence"]
        self.assertEqual(body["candidates_written"], 3)
        self.assertEqual(body["confirmed_variables_added"], 0)
        self.assertEqual(body["pending_created"], 0)
        self.assertTrue(all(row["persisted"] for row in list_manual_intake_candidates(conn, ticker="300308.SZ")))


if __name__ == "__main__":
    unittest.main()
