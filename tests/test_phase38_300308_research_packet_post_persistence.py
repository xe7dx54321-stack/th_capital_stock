import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "jobs", ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "verification", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from persist_phase38_300308_targeted_candidates import build_payload as persist_candidates
from validate_phase38_300308_research_packet_post_persistence import build_payload
from phase38_helpers import make_phase38_conn


class Phase38300308ResearchPacketPostPersistenceTests(unittest.TestCase):
    def test_revalidation_strengthens_without_pending(self):
        conn = make_phase38_conn()
        persist_candidates(conn, mode="execute", limit=5)
        payload = build_payload(conn)
        body = payload["research_packet_post_persistence"]
        self.assertEqual(body["quality_delta"], "strengthened_with_new_supporting_evidence")
        self.assertEqual(body["new_pending_created"], 0)
        self.assertFalse(body["promotion_allowed"])
        self.assertIn("supplier_share", body["still_missing"])


if __name__ == "__main__":
    unittest.main()
