import sqlite3
import sys
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_claim_graph import ensure_claim_graph_tables
from smr_filings_ingestion import seed_filing_document
from smr_financial_table_extraction import extract_field_level_fundamentals
from smr_fundamentals import build_fundamentals_snapshot, latest_fundamentals_snapshot
from smr_paper_portfolio import ensure_paper_portfolio_tables
from smr_portfolio_risk import evaluate_portfolio_risk


class Phase7FinancialTableExtractionTests(unittest.TestCase):
    def make_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(":memory:")
        ensure_claim_graph_tables(conn)
        ensure_paper_portfolio_tables(conn)
        conn.executescript(
            """
            CREATE TABLE daily_bar (
                ts_code TEXT,
                market TEXT,
                trade_date TEXT,
                close REAL
            );
            CREATE TABLE factor_daily (
                ts_code TEXT,
                trade_date TEXT,
                factor_name TEXT,
                factor_value REAL
            );
            """
        )
        return conn

    def test_hk_fundamentals_extract_field_level_details_and_missing_reasons(self):
        conn = self.make_conn()
        today = datetime.now().strftime("%Y-%m-%d")
        seed_filing_document(
            conn,
            ticker="00700.HK",
            title="00700.HK interim report",
            body=(
                "单位：百万元 港币\n"
                "营业收入 300,000\n"
                "毛利润 120,000\n"
                "经营利润 90,000\n"
                "归母净利润 80,000\n"
                "基本每股收益 1.25\n"
                "稀释每股收益 1.20\n"
                "经营活动产生的现金流量净额 60,000\n"
                "购建固定资产、无形资产和其他长期资产支付的现金 10,000\n"
                "现金及现金等价物 500,000\n"
                "总债务 100,000\n"
                "股东权益 900,000\n"
            ),
            source_key="hkex_announcement",
            market="H",
            filing_type="interim_report",
            published_at=today,
        )

        snapshot = build_fundamentals_snapshot(conn, "00700.HK", prefer_live=False)
        latest = latest_fundamentals_snapshot(conn, "00700.HK")

        self.assertEqual(snapshot["ticker"], "00700.HK")
        self.assertTrue(snapshot["field_details"]["revenue"]["source_evidence_id"])
        self.assertEqual(snapshot["field_details"]["revenue"]["currency"], "HKD")
        self.assertEqual(snapshot["field_details"]["revenue"]["missing_reason"], None)
        self.assertIn("free_cash_flow", snapshot["field_details"])
        self.assertEqual(snapshot["freshness_status"], "fresh")
        self.assertEqual(latest["snapshot_id"], snapshot["snapshot_id"])

    def test_a_share_fundamentals_expose_missing_reason_when_field_absent(self):
        conn = self.make_conn()
        today = datetime.now().strftime("%Y-%m-%d")
        seed_filing_document(
            conn,
            ticker="300308.SZ",
            title="300308.SZ annual report",
            body=(
                "单位：万元\n"
                "营业收入 120000\n"
                "归母净利润 24000\n"
                "基本每股收益 0.85\n"
                "经营活动产生的现金流量净额 18000\n"
            ),
            source_key="cninfo_announcement",
            market="A",
            filing_type="annual_report",
            published_at=today,
        )

        snapshot = build_fundamentals_snapshot(conn, "300308.SZ", prefer_live=False)

        self.assertEqual(snapshot["market"], "A")
        self.assertTrue(snapshot["field_details"]["revenue"]["source_evidence_id"])
        self.assertIn("gross_profit", snapshot["missing_fields"])
        self.assertIn(snapshot["field_details"]["gross_profit"]["missing_reason"], {"field_not_found", "parse_failed", "table_not_found"})
        self.assertGreaterEqual(snapshot["field_details"]["operating_cash_flow"]["confidence"], 0.0)

    def test_portfolio_risk_exposes_projected_exposure_and_risk_adjusted_sizing(self):
        conn = self.make_conn()
        today = datetime.now().strftime("%Y-%m-%d")
        conn.execute("INSERT INTO daily_bar VALUES ('NVDA', 'US', ?, 100.0)", (today,))
        conn.execute(
            "INSERT INTO paper_portfolio_positions (position_id, ticker, market, quantity, avg_cost, position_pct, status, opened_at, closed_at, source_recommendation_id, metadata_json) VALUES ('pos-1', 'AVGO', 'US', 1, 100.0, 4.5, 'open', ?, NULL, 'rec-avgo', '{}')",
            (today,),
        )
        result = evaluate_portfolio_risk(
            conn,
            ticker="NVDA",
            watchlist_item={"ticker": "NVDA", "market": "US", "theme": "semiconductor_compute", "sector": "semiconductor_compute", "max_position_pct": 2.0},
            suggested_position_pct=2.0,
            max_position_pct=5.0,
            watchlist_name="ai_core",
            watchlist_items=[
                {"ticker": "NVDA", "market": "US", "theme": "semiconductor_compute", "sector": "semiconductor_compute", "max_position_pct": 2.0},
                {"ticker": "AVGO", "market": "US", "theme": "semiconductor_compute", "sector": "semiconductor_compute", "max_position_pct": 2.0},
            ],
        )

        self.assertIn("projected_exposure", result)
        self.assertIn("projected_exposure_after_sizing", result)
        self.assertIn("risk_adjusted_sizing", result)
        self.assertGreaterEqual(result["projected_exposure"]["single_name"], 0.0)

    def test_phase8_hk_synonyms_extract_real_chinese_fields(self):
        conn = self.make_conn()
        today = datetime.now().strftime("%Y-%m-%d")
        seed_filing_document(
            conn,
            ticker="09988.HK",
            title="09988.HK annual results",
            body=(
                "单位：人民币百万元\n"
                "客户合同收入 941,168\n"
                "毛利 365,022\n"
                "经营利润 165,028\n"
                "本公司权益持有人应占盈利 130,123\n"
                "每股基本盈利 8.21\n"
                "每股摊薄盈利 8.05\n"
                "经营活动所得现金净额 198,000\n"
                "银行结余及现金 600,000\n"
                "借款 180,000\n"
                "本公司权益持有人应占权益 1,200,000\n"
            ),
            source_key="hkex_announcement",
            market="H",
            filing_type="annual_results",
            published_at=today,
        )

        extracted = extract_field_level_fundamentals(conn, "09988.HK", market="H")

        self.assertIsNotNone(extracted["field_values"].get("revenue"))
        self.assertIsNotNone(extracted["field_values"].get("net_income"))
        self.assertIsNotNone(extracted["field_values"].get("eps_basic"))
        self.assertEqual(extracted["field_details"]["revenue"]["currency"], "CNY")
        self.assertTrue(extracted["field_details"]["revenue"]["source_evidence_id"])

    def test_phase8_percent_not_amount_sanity_check(self):
        conn = self.make_conn()
        today = datetime.now().strftime("%Y-%m-%d")
        seed_filing_document(
            conn,
            ticker="00700.HK",
            title="00700.HK results",
            body=(
                "单位：港币百万元\n"
                "毛利率 48%\n"
                "收入 660,000\n"
                "本公司拥有人应占利润 115,000\n"
            ),
            source_key="hkex_announcement",
            market="H",
            filing_type="annual_results",
            published_at=today,
        )

        extracted = extract_field_level_fundamentals(conn, "00700.HK", market="H")

        self.assertIsNone(extracted["field_values"].get("gross_profit"))
        self.assertIn(extracted["field_missing_reasons"]["gross_profit"], {"field_not_found", "parse_failed"})
        self.assertIsNotNone(extracted["field_values"].get("revenue"))


if __name__ == "__main__":
    unittest.main()
