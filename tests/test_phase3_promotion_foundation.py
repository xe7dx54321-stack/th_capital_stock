import sqlite3
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_claim_graph import ensure_claim_graph_tables, upsert_evidence
from smr_consensus_proxy import build_consensus_revision_proxy
from smr_data_health import ensure_data_health_tables
from smr_decision import current_decision_status
from smr_filings_ingestion import export_filings_to_evidence, seed_filing_document, update_filings_health_rows
from smr_news_ingestion import export_news_to_evidence, seed_news_item, update_news_health_rows
from smr_recommendation_candidate import build_recommendation_candidate
from smr_recommendation_promotion import evaluate_promotion
from smr_research_quality import lint_report


def conn() -> sqlite3.Connection:
    db = sqlite3.connect(":memory:")
    db.row_factory = sqlite3.Row
    ensure_data_health_tables(db)
    ensure_claim_graph_tables(db)
    return db


def passing_health_snapshot() -> dict:
    return {
        "overall_status": "fresh",
        "items": [
            {"data_type": "daily_bar", "market": "A", "freshness_status": "fresh", "blocking_level": "none"},
            {"data_type": "daily_bar", "market": "H", "freshness_status": "fresh", "blocking_level": "none"},
            {"data_type": "daily_bar", "market": "US", "freshness_status": "fresh", "blocking_level": "none"},
            {"data_type": "news", "market": "US", "freshness_status": "fresh", "blocking_level": "none"},
            {
                "data_type": "filings",
                "market": "US",
                "freshness_status": "fresh",
                "blocking_level": "none",
                "metadata": {"scope": "watchlist", "ticker": "NVDA"},
            },
        ],
    }


class Phase3IngestionTests(unittest.TestCase):
    def test_news_seed_dedupe_health_and_secondary_evidence(self):
        db = conn()
        seed_news_item(db, "NVDA raises AI guidance", body="Management raised AI revenue outlook.", source_key="manual_news", ticker="NVDA")
        seed_news_item(db, "NVDA raises AI guidance", body="Duplicate repost.", source_key="manual_repost", ticker="NVDA")
        row = db.execute("SELECT COUNT(*) FROM news_items").fetchone()
        self.assertEqual(row[0], 1)

        health = update_news_health_rows(db)
        self.assertEqual(health["overall_status"], "fresh")
        evidence = export_news_to_evidence(db)
        self.assertEqual(evidence["exported"], 1)
        ev = db.execute("SELECT source_type, source_quality FROM evidence_items").fetchone()
        self.assertEqual(ev[0], "news")
        self.assertEqual(ev[1], "secondary")

    def test_filing_seed_chunks_health_and_primary_evidence(self):
        db = conn()
        seed_filing_document(
            db,
            ticker="NVDA",
            title="NVDA 10-Q earnings release",
            body="Revenue increased materially. Risk factors include supply constraints and customer concentration.",
            source_key="sec_filing_document",
        )
        self.assertEqual(db.execute("SELECT COUNT(*) FROM filing_documents").fetchone()[0], 1)
        self.assertGreaterEqual(db.execute("SELECT COUNT(*) FROM document_chunks").fetchone()[0], 1)
        health = update_filings_health_rows(db)
        self.assertEqual(health["overall_status"], "fresh")
        evidence = export_filings_to_evidence(db)
        self.assertEqual(evidence["exported"], 1)
        ev = db.execute("SELECT source_type, source_quality FROM evidence_items").fetchone()
        self.assertEqual(ev[0], "filing")
        self.assertEqual(ev[1], "primary")


class Phase3PromotionTests(unittest.TestCase):
    def test_consensus_proxy_quality_remains_internal(self):
        db = conn()
        upsert_evidence(
            db,
            {
                "evidence_id": "ev_primary",
                "source_key": "sec_filing_document",
                "source_type": "filing",
                "source_quality": "primary",
                "source_status": "active",
                "published_at": None,
                "ingested_at": None,
                "text_excerpt": "Guidance raised.",
                "url_or_doc_id": "doc",
                "metadata": {},
            },
        )
        upsert_evidence(
            db,
            {
                "evidence_id": "ev_news",
                "source_key": "manual_news",
                "source_type": "news",
                "source_quality": "secondary",
                "source_status": "active",
                "published_at": None,
                "ingested_at": None,
                "text_excerpt": "Analysts raised estimates.",
                "url_or_doc_id": "url",
                "metadata": {},
            },
        )
        proxy = build_consensus_revision_proxy(
            db,
            "NVDA 2026E EPS 1.20 -> 1.45 guidance raise beat higher",
            evidence_ids=["ev_primary", "ev_news"],
            ticker="NVDA",
            method="guidance_change",
        )
        self.assertFalse(proxy["is_official_consensus"])
        self.assertEqual(proxy["proxy_quality"], "strong")
        self.assertTrue(proxy["usable_for_promotion"])

    def test_lint_warn_explains_promotion_blocking(self):
        lint = lint_report(
            "buy NVDA. Bear case exists. kill condition: thesis breaks. position 2%. risk noted.",
            dashboard_summary={
                "action": "buy NVDA",
                "portfolio_action_plan": {"initial_action": {"buy": {"amount_cny": 10000}}},
                "valuation_snapshot": {"allowed_usage": "context_only"},
            },
            freshness_gate_result={"status": "pass"},
            evidence_check_result={"severity": "pass", "recommendation_allowed": True},
        )
        issues = {item["code"]: item for item in lint.issues}
        self.assertIn("VALUATION_CONTEXT_ONLY", issues)
        self.assertTrue(issues["VALUATION_CONTEXT_ONLY"]["blocks_promotion"])
        self.assertTrue(issues["VALUATION_CONTEXT_ONLY"]["required_fix"])

    def test_promotion_failure_reports_missing_requirements(self):
        result = evaluate_promotion(
            dashboard_summary={"action": "buy NVDA", "ticker": "NVDA"},
            data_health_snapshot={"items": []},
            evidence_check_snapshot={},
            claim_graph_snapshot={},
            valuation_snapshot={"allowed_usage": "context_only"},
            consensus_proxy={"proxy_quality": "weak", "usable_for_promotion": False},
            bear_case={},
            risk_snapshot={},
            lint_result={"max_severity": "info", "issues": []},
        )
        self.assertFalse(result.allowed)
        self.assertIn("data_health_snapshot", result.missing_requirements)
        self.assertTrue(result.required_fixes)

    def test_promotion_success_writes_pending_review_ledger(self):
        db = conn()
        result = evaluate_promotion(
            db,
            report_id="report-1",
            recommendation_id="rec-1",
            dashboard_summary={
                "action": "buy NVDA",
                "ticker": "NVDA",
                "suggested_position_pct": 2.0,
                "max_position_pct": 5.0,
                "kill_triggers": ["Primary evidence breaks thesis"],
            },
            data_health_snapshot=passing_health_snapshot(),
            evidence_check_snapshot={"severity": "pass", "evidence_summary": {"source_path_count": 2, "primary_anchor_count": 1}},
            claim_graph_snapshot={"unsupported_core_claims": [], "counter_evidence_count": 1},
            valuation_snapshot={"allowed_usage": "supporting_evidence"},
            fundamentals_snapshot={"freshness_status": "fresh", "missing_fields": []},
            consensus_proxy={"proxy_quality": "strong", "usable_for_promotion": True, "is_official_consensus": False},
            bear_case={"bear_case_claims": [{"claim_text": "risk"}], "deal_breakers": ["break"]},
            risk_snapshot={"status": "pass"},
            lint_result={"max_severity": "info", "issues": []},
            write_ledger=True,
        )
        self.assertTrue(result.allowed)
        self.assertEqual(result.to_status, "pending_human_review")
        self.assertEqual(current_decision_status(db, "rec-1"), "pending_human_review")

    def test_candidate_builder_downgrades_context_only_valuation(self):
        candidate = build_recommendation_candidate(
            recommendation_id="rec-2",
            ticker="NVDA",
            valuation_snapshot={"allowed_usage": "context_only"},
            consensus_proxy={"proxy_quality": "strong", "usable_for_promotion": True},
            bear_case={"bear_case_strength": "medium", "deal_breakers": ["break"]},
            risk_snapshot={"status": "pass"},
            market_signal={"signal": "positive"},
            promotion_result={"allowed": True, "to_status": "pending_human_review"},
        )
        self.assertEqual(candidate["action"], "watch")
        self.assertNotEqual(candidate["status"], "pending_human_review")


if __name__ == "__main__":
    unittest.main()
