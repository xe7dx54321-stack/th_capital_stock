import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_cn_tender_procurement import classify_tender_evidence_type, normalize_cn_tender_result


class Phase24TenderSchemaTests(unittest.TestCase):
    def test_tender_notice_is_not_award(self):
        item = normalize_cn_tender_result(
            {"title": "中际旭创 AI服务器采购招标公告", "source_url": "https://example.com/tender", "source_type": "filing"},
            ticker="300308.SZ",
        )
        self.assertEqual(item["evidence_type"], "procurement_notice")
        self.assertNotEqual(item["evidence_strength"], "confirmed_award")

    def test_procurement_notice_is_not_procurement_award(self):
        self.assertEqual(classify_tender_evidence_type("海光信息 采购公告 算力服务器"), "procurement_notice")
        self.assertNotEqual(classify_tender_evidence_type("海光信息 采购公告 算力服务器"), "procurement_award")

    def test_customer_capex_is_not_company_order(self):
        item = normalize_cn_tender_result(
            {"title": "某客户智算中心服务器扩容项目", "source_url": "https://example.com/capex"},
            ticker="688041.SH",
        )
        self.assertEqual(item["evidence_type"], "customer_capex")
        self.assertIn("not company-specific order", "; ".join(item["limitations"]))

    def test_news_and_rumor_are_not_confirmed(self):
        news = normalize_cn_tender_result(
            {"title": "新闻转载 科大讯飞中标项目", "source_url": "https://example.com/news", "source_type": "news"},
            ticker="002230.SZ",
        )
        rumor = normalize_cn_tender_result(
            {"title": "网传科大讯飞获得大订单", "source_url": "https://example.com/rumor"},
            ticker="002230.SZ",
        )
        self.assertEqual(news["allowed_usage"], "context_only")
        self.assertEqual(rumor["evidence_strength"], "blocked")


if __name__ == "__main__":
    unittest.main()
