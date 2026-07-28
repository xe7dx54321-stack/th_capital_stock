from __future__ import annotations

import unittest

from smr_app.research.evaluation import build_stock_deep_dive_scorecard, evaluate_stock_deep_dive_case


def healthy_packet() -> dict:
    evidence_id = "ev_primary_001"
    return {
        "schema_version": "2.0",
        "ticker": "TEST",
        "claims": [
            {
                "claim_id": "claim_001",
                "statement": "报告期 2026Q1，营业收入为 100.00 美元。",
                "evidence_ids": [evidence_id],
                "source_paths": ["fundamentals.revenue"],
            }
        ],
        "scenarios": [],
        "quality": {
            "readiness": "research_ready",
            "blockers": [],
            "usable_evidence_ids": [evidence_id],
            "quarantined_fields": [],
            "report_gate": {"report_status": "research_ready"},
            "report_validation": {"status": "passed", "errors": []},
        },
        "datasets": {
            "evidence": {
                "items": [
                    {
                        "evidence_id": evidence_id,
                        "source_type": "filing",
                        "source_quality": "primary",
                        "published_at": "2026-07-20",
                    }
                ]
            }
        },
    }


class StockDeepDiveEvaluationTests(unittest.TestCase):
    def test_healthy_case_passes(self) -> None:
        packet = healthy_packet()
        result = evaluate_stock_deep_dive_case(
            case={
                "ticker": "TEST", "market": "US", "role": "fixture",
                "expected_statuses": ["research_ready"], "minimum_approved_claims": 1,
                "minimum_report_characters": 20,
            },
            run={"run_id": "run_1", "status": "completed"},
            packet=packet,
            report="# 个股深度研究\n\n报告期 2026Q1，营业收入为 100.00 美元。[ev_primary_001]",
        )
        self.assertTrue(result["passed"])
        self.assertEqual(100, result["score"])

    def test_quarantined_field_and_secondary_source_fail(self) -> None:
        packet = healthy_packet()
        packet["quality"]["quarantined_fields"] = ["fundamentals.revenue"]
        packet["datasets"]["evidence"]["items"][0]["source_type"] = "news"
        packet["datasets"]["evidence"]["items"][0]["source_quality"] = "secondary"
        result = evaluate_stock_deep_dive_case(
            case={"ticker": "TEST", "market": "US", "role": "fixture", "minimum_report_characters": 1},
            run={"run_id": "run_1", "status": "completed"},
            packet=packet,
            report="有效报告",
        )
        codes = {item["code"] for item in result["findings"]}
        self.assertFalse(result["passed"])
        self.assertIn("quarantined_field_leak", codes)
        self.assertIn("non_primary_source_type", codes)
        self.assertIn("non_primary_source_quality", codes)

    def test_scorecard_counts_unsupported_conclusions(self) -> None:
        result = {
            "passed": False,
            "score": 90,
            "findings": [
                {"code": "stale_data_promoted", "message": "bad", "hard": True},
            ],
        }
        scorecard = build_stock_deep_dive_scorecard([result])
        self.assertEqual(1, scorecard["unsupported_conclusion_count"])
        self.assertFalse(scorecard["passed"])


if __name__ == "__main__":
    unittest.main()
