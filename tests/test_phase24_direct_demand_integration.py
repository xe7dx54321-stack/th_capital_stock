import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_cn_tender_procurement import normalize_cn_tender_result
from smr_direct_demand_evidence import direct_demand_item_from_tender_candidate, summarize_demand_evidence
from smr_tender_evidence_linkage import tender_item_to_evidence_candidate


class Phase24DirectDemandIntegrationTests(unittest.TestCase):
    def test_award_enters_direct_demand_but_notice_does_not_confirm(self):
        award = tender_item_to_evidence_candidate(
            normalize_cn_tender_result(
                {"title": "海光信息 中标结果公告", "body": "采购人 某客户 算力服务器项目", "source_url": "https://example.com/award"},
                ticker="688041.SH",
            )
        )
        notice = tender_item_to_evidence_candidate(
            normalize_cn_tender_result({"title": "海光信息 采购公告", "source_url": "https://example.com/notice"}, ticker="688041.SH")
        )
        award_item = direct_demand_item_from_tender_candidate(award)
        notice_item = direct_demand_item_from_tender_candidate(notice)
        self.assertEqual(award_item["demand_strength"], "confirmed_order")
        self.assertNotEqual(notice_item["demand_strength"], "confirmed_order")
        summary = summarize_demand_evidence("688041.SH", [award_item, notice_item])
        self.assertEqual(summary["confirmed_order_count"], 1)


if __name__ == "__main__":
    unittest.main()
