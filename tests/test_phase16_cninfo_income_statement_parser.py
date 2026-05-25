import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_cninfo_table_parser import (
    detect_income_statement_section,
    extract_income_statement_fields_from_chunks,
    extract_income_statement_fields_from_text,
)


class Phase16CninfoIncomeStatementParserTests(unittest.TestCase):
    def test_detects_cninfo_income_statement_titles(self):
        for title in ["合并利润表", "主要会计数据和财务指标", "Consolidated Income Statement"]:
            self.assertTrue(detect_income_statement_section(title)["table_detected"])

    def test_revenue_and_cost_derive_gross_profit(self):
        text = """
        合并利润表
        单位：万元
        营业收入 120,000
        营业成本 80,000
        """
        result = extract_income_statement_fields_from_text(text, source_evidence_id="ev_rev", source_chunk_id="chunk_cn")
        self.assertEqual(result["field_status"]["revenue"]["value"], 1_200_000_000.0)
        self.assertEqual(result["field_status"]["gross_profit"]["status"], "derived")
        self.assertEqual(result["field_status"]["gross_profit"]["value"], 400_000_000.0)
        self.assertEqual(result["field_status"]["gross_profit"]["input_evidence_ids"], ["ev_rev", "ev_rev"])

    def test_direct_gross_profit_extraction(self):
        text = "合并利润表\n单位：百万元\n营业总收入 900\n毛利润 300"
        result = extract_income_statement_fields_from_text(text, source_evidence_id="ev_cn")
        self.assertEqual(result["field_status"]["gross_profit"]["status"], "extracted")
        self.assertEqual(result["field_status"]["gross_profit"]["value"], 300_000_000.0)

    def test_percentage_not_amount(self):
        text = "合并利润表\n单位：万元\n营业收入同比增长 48%\n毛利率 22%"
        result = extract_income_statement_fields_from_text(text, source_evidence_id="ev_cn")
        self.assertEqual(result["field_status"]["revenue"]["status"], "missing")
        self.assertEqual(result["field_status"]["gross_profit"]["status"], "missing")

    def test_consolidated_preferred_over_parent_company(self):
        chunks = [
            {
                "chunk_id": "parent",
                "evidence_id": "ev_parent",
                "text": "母公司利润表\n单位：万元\n营业收入 10,000\n营业成本 8,000",
            },
            {
                "chunk_id": "consolidated",
                "evidence_id": "ev_con",
                "text": "合并利润表\n单位：万元\n营业收入 120,000\n营业成本 80,000",
            },
        ]
        result = extract_income_statement_fields_from_chunks(chunks, ticker="300308.SZ")
        self.assertEqual(result["scope"], "consolidated")
        self.assertEqual(result["field_status"]["revenue"]["source_evidence_id"], "ev_con")

    def test_parent_company_scope_is_context_only(self):
        result = extract_income_statement_fields_from_text(
            "母公司利润表\n单位：万元\n营业收入 10,000",
            source_evidence_id="ev_parent",
        )
        self.assertEqual(result["scope"], "parent_company")
        self.assertEqual(result["field_status"]["revenue"]["allowed_usage"], "context_only")


if __name__ == "__main__":
    unittest.main()
