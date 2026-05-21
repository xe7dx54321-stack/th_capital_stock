import sqlite3
import sys
import unittest
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIB_DIR = ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_claim_graph import claim_graph_summary, ensure_claim_graph_tables, link_claim_evidence, upsert_claim, upsert_evidence
from smr_evidence_quality import evidence_quality_summary, update_evidence_quality_scores
from smr_recommendation_promotion import evaluate_promotion


class EvidenceQualityTests(unittest.TestCase):
    def test_low_quality_evidence_does_not_support_core_claim(self):
        conn = sqlite3.connect(":memory:")
        ensure_claim_graph_tables(conn)
        today = datetime.now().strftime("%Y-%m-%d")
        upsert_claim(
            conn,
            {
                "claim_id": "claim-low-quality",
                "report_id": "report-quality",
                "recommendation_id": "rec-quality",
                "ticker": "NVDA",
                "claim_text": "NVDA demand is accelerating materially.",
                "claim_type": "revenue_growth",
                "importance": "core",
                "stance": "base",
                "confidence": 0.5,
            },
        )
        for index in range(2):
            evidence_id = f"ev-low-{index}"
            upsert_evidence(
                conn,
                {
                    "evidence_id": evidence_id,
                    "source_key": "low_quality_blog",
                    "source_type": "news",
                    "source_quality": "tertiary",
                    "source_status": "active",
                    "published_at": today,
                    "ingested_at": today,
                    "text_excerpt": "Market chatter says things may be better.",
                    "url_or_doc_id": f"https://example.com/{index}",
                    "metadata": {"ticker": "NVDA"},
                },
            )
            link_claim_evidence(conn, "claim-low-quality", evidence_id, "supports", 0.5, "weak support")

        update_evidence_quality_scores(conn, ticker="NVDA")
        summary = claim_graph_summary(conn, "report-quality")
        result = evaluate_promotion(
            dashboard_summary={"action": "buy NVDA", "ticker": "NVDA", "suggested_position_pct": 1.0, "max_position_pct": 2.0},
            data_health_snapshot={"items": [{"data_type": "daily_bar", "freshness_status": "fresh", "blocking_level": "none"}]},
            evidence_check_snapshot={"evidence_summary": {"source_path_count": 2, "primary_anchor_count": 1}},
            claim_graph_snapshot=summary,
            valuation_snapshot={"allowed_usage": "promotion_eligible"},
            consensus_proxy={"proxy_quality": "strong", "usable_for_promotion": True},
            fundamentals_snapshot={"freshness_status": "fresh", "missing_fields": []},
            bear_case={"bear_case_claims": ["bear"], "deal_breakers": ["kill"]},
            risk_snapshot={"status": "pass"},
            lint_result={"max_severity": "info", "issues": []},
        )

        self.assertTrue(summary["low_quality_core_claims"])
        self.assertIn("core_claim_evidence_quality", result.missing_requirements)

    def test_primary_live_evidence_can_be_usable_for_promotion(self):
        conn = sqlite3.connect(":memory:")
        ensure_claim_graph_tables(conn)
        today = datetime.now().strftime("%Y-%m-%d")
        upsert_evidence(
            conn,
            {
                "evidence_id": "ev-primary-live",
                "source_key": "sec_filing_document",
                "source_type": "filing",
                "source_quality": "primary",
                "source_status": "active",
                "published_at": today,
                "ingested_at": today,
                "text_excerpt": "NVDA revenue increased 30 percent and gross margin improved with cash flow growth.",
                "url_or_doc_id": "https://sec.example/doc",
                "metadata": {"ticker": "NVDA", "live": True},
            },
        )

        metrics = update_evidence_quality_scores(conn, ticker="NVDA")
        quality = evidence_quality_summary(conn, ["ev-primary-live"])

        self.assertEqual(metrics["updated"], 1)
        self.assertGreaterEqual(quality["usable_for_promotion_count"], 1)
        self.assertGreaterEqual(quality["avg_quality_score"], 0.68)


if __name__ == "__main__":
    unittest.main()
