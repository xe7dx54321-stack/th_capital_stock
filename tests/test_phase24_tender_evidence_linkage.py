import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_cn_tender_procurement import normalize_cn_tender_result
from smr_tender_evidence_linkage import load_tender_evidence_candidates, tender_item_to_evidence_candidate, upsert_tender_evidence_candidate


class Phase24TenderEvidenceLinkageTests(unittest.TestCase):
    def test_source_url_required_and_deduped(self):
        item = normalize_cn_tender_result(
            {"title": "海光信息 中标结果公告", "source_url": "https://example.com/award"},
            ticker="688041.SH",
        )
        candidate = tender_item_to_evidence_candidate(item)
        conn = sqlite3.connect(":memory:")
        self.assertTrue(upsert_tender_evidence_candidate(conn, candidate))
        self.assertTrue(upsert_tender_evidence_candidate(conn, candidate))
        self.assertEqual(len(load_tender_evidence_candidates(conn, "688041.SH")), 1)

        no_url = tender_item_to_evidence_candidate({**item, "source_url": None})
        self.assertFalse(upsert_tender_evidence_candidate(conn, no_url))


if __name__ == "__main__":
    unittest.main()
