import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "jobs", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase43_manual_intake_candidates import build_payload
from phase42_helpers import make_phase42_conn
from smr_manual_intake_candidate_generator import list_manual_intake_candidates


class Phase43ManualIntakeCandidateGeneratorTests(unittest.TestCase):
    def test_default_payloads_generate_candidates_not_confirmed(self):
        payload = build_payload(make_phase42_conn(), ticker="300308.SZ", mode="dry_run")
        body = payload["manual_intake_candidate_generation"]
        self.assertEqual(body["payloads_checked"], 3)
        self.assertEqual(body["candidates_created"], 3)
        self.assertEqual(body["rejection_records_created"], 0)
        official = next(row for row in body["candidate_rows"] if row["evidence_type"] == "official_consensus")
        self.assertEqual(official["confirmation_status"], "candidate_not_confirmed")
        self.assertFalse(official["usable_for_promotion"])
        self.assertFalse(official["is_confirmed"])

    def test_internal_proxy_pretending_official_consensus_is_rejected(self):
        payload = build_payload(make_phase42_conn(), ticker="300308.SZ", sample="bad_consensus_internal_proxy", mode="dry_run")
        body = payload["manual_intake_candidate_generation"]
        self.assertEqual(body["candidates_created"], 0)
        self.assertEqual(body["rejection_records_created"], 1)
        reasons = body["rejection_rows"][0]["rejection_reasons"]
        self.assertIn("internal_proxy_cannot_be_official_consensus", reasons)

    def test_execute_writes_candidates_without_promotion(self):
        conn = make_phase42_conn()
        payload = build_payload(conn, ticker="300308.SZ", mode="execute")
        body = payload["manual_intake_candidate_generation"]
        self.assertEqual(body["candidates_written"], 3)
        rows = list_manual_intake_candidates(conn, ticker="300308.SZ")
        self.assertEqual(len(rows), 3)
        self.assertFalse(any(row["usable_for_promotion"] for row in rows))


if __name__ == "__main__":
    unittest.main()
