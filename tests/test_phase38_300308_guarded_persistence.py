import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "jobs", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from persist_phase38_300308_targeted_candidates import build_payload
from phase38_helpers import make_phase38_conn


class Phase38300308GuardedPersistenceTests(unittest.TestCase):
    def test_guarded_persistence_limit_and_promotion_boundary(self):
        conn = make_phase38_conn()
        dry_run = build_payload(conn, mode="dry_run", limit=5)["persistence_result"]
        self.assertEqual(dry_run["selected_for_persistence"], 5)
        self.assertEqual(dry_run["candidates_written"], 0)
        execute = build_payload(conn, mode="execute", limit=5)["persistence_result"]
        self.assertEqual(execute["attempted_to_write"], 5)
        self.assertEqual(execute["candidates_written"], 5)
        self.assertEqual(execute["usable_for_promotion_true"], 0)
        self.assertEqual(execute["new_pending_created"], 0)


if __name__ == "__main__":
    unittest.main()
