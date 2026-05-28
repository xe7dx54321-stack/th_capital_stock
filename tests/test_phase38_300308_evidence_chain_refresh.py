import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "jobs", ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase38_300308_evidence_chain_refresh import build_payload as build_refresh
from persist_phase38_300308_targeted_candidates import build_payload as persist_candidates
from phase38_helpers import make_phase38_conn


class Phase38300308EvidenceChainRefreshTests(unittest.TestCase):
    def test_evidence_chain_before_after_is_explainable(self):
        conn = make_phase38_conn()
        before = build_refresh(conn)["evidence_chain_refresh"]
        persisted = persist_candidates(conn, mode="execute", limit=5)["persistence_result"]
        after = build_refresh(conn)["evidence_chain_refresh"]
        self.assertEqual(persisted["candidates_written"], 5)
        self.assertEqual(after["new_candidates_written"], persisted["candidates_written"])
        self.assertEqual(after["evidence_after"], before["evidence_after"] + persisted["candidates_written"])
        self.assertEqual(after["sensitive_confirmed_added"], 0)
        self.assertEqual(after["usable_for_promotion_true"], 0)


if __name__ == "__main__":
    unittest.main()
