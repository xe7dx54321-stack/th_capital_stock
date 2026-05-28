import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for path in (ROOT / "08_scripts" / "reporting", ROOT / "08_scripts" / "lib", ROOT / "tests"):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase39_human_research_review_checklist import build_payload
from phase39_helpers import make_phase39_conn


class Phase39HumanReviewChecklistTests(unittest.TestCase):
    def test_checklist_has_evidence_ids_and_non_goals(self):
        payload = build_payload(make_phase39_conn(), "300308.SZ")
        body = payload["human_research_review_checklist"]
        self.assertTrue(body["explicit_non_goals"])
        self.assertTrue(any("Do not create paper order" in item for item in body["explicit_non_goals"]))
        items = body["checklist_items"]
        evidence_refs = [ref for item in items for ref in item.get("evidence_to_review", [])]
        self.assertTrue(evidence_refs)
        self.assertTrue(any("supplier_share" in item.get("evidence_gap", []) for item in items))
        self.assertFalse(payload["safety"]["checklist_is_trade_review"])


if __name__ == "__main__":
    unittest.main()
