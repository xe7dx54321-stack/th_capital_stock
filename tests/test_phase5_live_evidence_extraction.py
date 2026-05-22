import sqlite3
import sys
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_claim_graph import ensure_claim_graph_tables, upsert_evidence
from smr_evidence_quality import update_evidence_quality_scores
from smr_filing_chunk_selector import classify_chunk_text, select_relevant_document_chunks
from smr_filings_ingestion import export_filings_to_evidence, seed_filing_document
from smr_news_ingestion import export_news_to_evidence, seed_news_item, upsert_news_item
from smr_promotion_debugger import explain_promotion_result
from smr_proxy_extraction import build_live_consensus_proxy, live_evidence_for_proxy


class Phase5LiveEvidenceExtractionTests(unittest.TestCase):
    def test_filing_chunk_selector_filters_administrative_chunks(self):
        conn = sqlite3.connect(":memory:")
        ensure_claim_graph_tables(conn)
        seed_filing_document(
            conn,
            ticker="NVDA",
            title="NVDA 8-K earnings release",
            source_key="sec_filing_document",
            body=(
                "Cover page source_url fetched_at signature exhibit index.\n\n"
                "Management discussion and outlook: NVIDIA revenue increased 69 percent. "
                "The company expects higher revenue next quarter and guidance points to stronger demand. "
                "Gross margin guidance improved and operating cash flow increased."
            ),
            market="US",
            filing_type="earnings_release",
        )

        chunks = select_relevant_document_chunks(conn, ticker="NVDA", limit=8)
        metrics = export_filings_to_evidence(conn, limit=8)
        evidence_metadata = conn.execute("SELECT metadata_json FROM evidence_items").fetchone()[0]

        self.assertTrue(chunks)
        self.assertGreaterEqual(metrics["exported"], 1)
        self.assertIn("investment_relevance_score", evidence_metadata)
        self.assertNotIn("noise_section:cover_page", evidence_metadata)

    def test_live_proxy_extraction_builds_internal_signal(self):
        conn = sqlite3.connect(":memory:")
        ensure_claim_graph_tables(conn)
        today = datetime.now().strftime("%Y-%m-%d")
        upsert_evidence(
            conn,
            {
                "evidence_id": "ev-nvda-guidance",
                "source_key": "sec_filing_document",
                "source_type": "filing",
                "source_quality": "primary",
                "source_status": "active",
                "published_at": today,
                "ingested_at": today,
                "text_excerpt": "NVDA revenue increased 69% and management raised guidance with higher gross margin outlook.",
                "url_or_doc_id": "https://sec.example/nvda",
                "metadata": {
                    "ticker": "NVDA",
                    "live": True,
                    "chunk_section_type": "guidance_outlook",
                    "investment_relevance_score": 0.92,
                    "usable_for_core_claim": True,
                    "usable_for_proxy_signal": True,
                },
            },
        )
        upsert_evidence(
            conn,
            {
                "evidence_id": "ev-nvda-earnings",
                "source_key": "sec_earnings_material",
                "source_type": "filing",
                "source_quality": "primary",
                "source_status": "active",
                "published_at": today,
                "ingested_at": today,
                "text_excerpt": "NVDA EPS beat expectations and revenue growth was above prior outlook.",
                "url_or_doc_id": "https://ir.example/nvda",
                "metadata": {
                    "ticker": "NVDA",
                    "live": True,
                    "chunk_section_type": "financial_statement",
                    "investment_relevance_score": 0.88,
                    "usable_for_core_claim": True,
                    "usable_for_proxy_signal": True,
                },
            },
        )
        update_evidence_quality_scores(conn, ticker="NVDA")

        proxy = build_live_consensus_proxy(conn, "NVDA")
        row = conn.execute("SELECT COUNT(*) FROM proxy_signal_items WHERE ticker='NVDA'").fetchone()

        self.assertFalse(proxy["is_official_consensus"])
        self.assertIn(proxy["proxy_quality"], {"medium", "strong"})
        self.assertGreaterEqual(proxy["proxy_signal_count"], 2)
        self.assertGreaterEqual(proxy.get("independent_source_count", 0), 1)
        self.assertEqual(
            proxy.get("proxy_metadata", {}).get("independent_source_count"),
            proxy.get("independent_source_count"),
        )
        self.assertGreaterEqual(row[0], 2)

    def test_news_export_preserves_ticker_metadata_for_proxy(self):
        conn = sqlite3.connect(":memory:")
        ensure_claim_graph_tables(conn)
        upsert_news_item(
            conn,
            {
                "news_id": "live-nvda-news",
                "title": "Nvidia forecast for growth exceeded estimates",
                "body": "Nvidia (NVDA) reported revenue above expectations and raised guidance.",
                "source_key": "yahoo_finance_rss",
                "published_at": datetime.now().strftime("%Y-%m-%d"),
                "tickers": ["NVDA"],
                "market": "US",
                "metadata": {"live": True, "provider": "yahoo_finance"},
            },
        )

        export_news_to_evidence(conn, limit=5)
        update_evidence_quality_scores(conn, ticker="NVDA")
        rows = live_evidence_for_proxy(conn, "NVDA", limit=5)
        proxy = build_live_consensus_proxy(conn, "NVDA")

        self.assertTrue(any(row["source_type"] == "news" for row in rows))
        self.assertGreaterEqual(proxy["proxy_signal_count"], 1)
        self.assertIn(proxy["proxy_quality"], {"weak", "medium", "strong"})

    def test_administrative_compensation_revenue_is_not_proxy_signal(self):
        profile = classify_chunk_text(
            "Departure of Directors; Compensatory Arrangements of Certain Officers. "
            "The fiscal year 2027 variable compensation plan uses specified revenue goals. "
            "Target award opportunity equals 200% of base salary and restricted stock units vest later.",
            source_key="sec_filing_document",
            title="NVDA 8-K director compensation",
            filing_type="sec_8k",
        )

        self.assertIn(profile["exclude_reason"], {"administrative_low_signal", "noise_section:administrative"})
        self.assertFalse(profile["usable_for_proxy_signal"])
        self.assertLess(profile["investment_relevance_score"], 0.55)

    def test_promotion_debugger_reports_minimum_fix_path(self):
        debug = explain_promotion_result(
            "NVDA",
            {
                "from_status": "observation_only",
                "allowed": False,
                "missing_requirements": ["consensus_proxy_quality", "fresh_valuation_price"],
                "required_fixes": ["build live proxy", "refresh price"],
            },
            proxy={"proxy_quality": "invalid", "proxy_signal_count": 0},
            fundamentals={"freshness_status": "fresh", "missing_fields": []},
            valuation={"allowed_usage": "blocked_due_to_stale_price"},
        )

        self.assertEqual(debug["blocking_factors"][0]["code"], "consensus_proxy_quality")
        self.assertTrue(debug["minimum_fix_path"])
        self.assertIn("proxy", debug["minimum_fix_path"][0])


if __name__ == "__main__":
    unittest.main()
