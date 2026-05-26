import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_cn_tender_query_planner import build_cn_tender_queries


class Phase24TenderQueryPlannerTests(unittest.TestCase):
    def test_target_tickers_generate_company_queries(self):
        for ticker, company in {"300308.SZ": "中际旭创", "688041.SH": "海光信息", "002230.SZ": "科大讯飞"}.items():
            queries = build_cn_tender_queries(ticker)
            self.assertGreaterEqual(len(queries), 10)
            self.assertTrue(all(company in row["query"] for row in queries if row.get("query")))
            self.assertTrue(any("算力" in row["query"] for row in queries))
            self.assertTrue(all(row.get("expected_evidence_type") for row in queries))

    def test_missing_company_name_blocks_query_plan(self):
        queries = build_cn_tender_queries("000000.SZ")
        self.assertEqual(queries[0]["query_type"], "missing_company_name")


if __name__ == "__main__":
    unittest.main()
