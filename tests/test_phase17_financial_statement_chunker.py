import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_financial_statement_chunker import (
    classify_financial_section,
    extract_financial_statement_chunks_from_source,
)


class Phase17FinancialStatementChunkerTests(unittest.TestCase):
    def test_hkex_balance_sheet_chunk_classification(self):
        text = """
        Consolidated Statement of Financial Position
        RMB million
        Assets 1,500,000
        Liabilities 300,000
        Equity attributable to equity holders of the Company 1,154,152
        Total equity 1,200,000
        """
        classified = classify_financial_section(text)
        self.assertEqual(classified["section_type"], "balance_sheet")
        self.assertGreaterEqual(classified["confidence"], 0.55)

    def test_cninfo_income_statement_chunk_extraction(self):
        text = """
        合并利润表
        单位：元
        营业收入 12,000,000,000
        营业成本 8,000,000,000
        利润总额 3,000,000,000
        合并资产负债表
        资产总计 20,000,000,000
        负债合计 5,000,000,000
        所有者权益合计 15,000,000,000
        """
        source = {"source_id": "cninfo_300308_fixture", "published_at": "2026-03-31", "title": "2025年年度报告", "source_url": "https://example.test/300308.pdf"}
        payload = extract_financial_statement_chunks_from_source("300308.SZ", source, text=text)
        section_types = {chunk["section_type"] for chunk in payload["chunks"]}
        self.assertIn("income_statement", section_types)
        self.assertIn("balance_sheet", section_types)
        self.assertEqual(payload["section_counts"]["income_statement"], 1)

    def test_noise_sections_are_not_financial_tables(self):
        self.assertEqual(classify_financial_section("Contents\n1 Definitions\n2 Corporate Information")["section_type"], "non_financial_section")
        self.assertEqual(classify_financial_section("Management Discussion and Analysis\nBusiness review without table values")["section_type"], "management_discussion")

    def test_notes_window_is_not_promoted_to_financial_highlights(self):
        text = """
        Notes to the Consolidated Financial Statements
        General information
        Financial Summary
        Consolidated Income Statement
        Revenues 100,000
        Gross profit 40,000
        Profit for the year 20,000
        """
        source = {"source_id": "hkex_fixture", "published_at": "2026-04-09", "title": "Annual Report 2025", "source_url": "https://example.test/00700.pdf"}
        payload = extract_financial_statement_chunks_from_source("00700.HK", source, text=text)
        titles = [chunk["section_title"] for chunk in payload["chunks"]]
        self.assertNotIn("Notes to the Consolidated Financial Statements", titles)

    def test_financial_highlights_do_not_become_income_statement(self):
        text = "主要会计数据和财务指标\n营业收入 100,000\n同比增长 40%\n基本每股收益 1.20"
        classified = classify_financial_section(text)
        self.assertEqual(classified["section_type"], "financial_highlights")


if __name__ == "__main__":
    unittest.main()
