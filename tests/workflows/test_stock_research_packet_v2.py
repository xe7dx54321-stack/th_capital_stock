from __future__ import annotations

import unittest

from smr_app.research.normalization import normalize_research_data
from smr_app.research.stock_packet import build_stock_research_packet


def evidence(evidence_id: str = "E001") -> dict:
    return {
        "items": [
            {
                "evidence_id": evidence_id,
                "source_key": "official_filing",
                "source_type": "official_filing",
                "source_quality": "official",
                "source_status": "active",
                "published_at": "2026-07-10",
                "url_or_doc_id": "doc-1",
                "text_excerpt": "公司披露了本期经营数据。",
                "quality_score": 0.95,
                "usable_for_core_claim": True,
            }
        ]
    }


def normalize(fundamentals: dict, evidence_data: dict | None = None) -> dict:
    return normalize_research_data(
        market="A",
        fundamentals=fundamentals,
        valuation={},
        evidence=evidence_data or evidence(),
        risk={"alerts": []},
        freshness={"status": "fresh", "blocking_level": "none"},
    )


class ResearchDataNormalizationTests(unittest.TestCase):
    def test_field_provenance_supplies_period_and_rejects_currency_mismatch(self) -> None:
        normalized = normalize(
            {
                "period": None,
                "revenue": 38_239_935_640.67,
                "net_income": 200_000_000.0,
                "source_evidence_ids": ["E001"],
                "field_details": {
                    "revenue": {"period": "2025FY", "normalized_unit": "CNY"},
                    "net_income": {"period": "2025FY", "normalized_unit": "USD"},
                },
            }
        )

        fundamentals = normalized["fundamentals"]
        self.assertEqual("2025FY", fundamentals["period"])
        self.assertEqual("valid", fundamentals["fields"]["revenue"]["status"])
        self.assertEqual("quarantined", fundamentals["fields"]["net_income"]["status"])
        self.assertIn("currency_unit_mismatch", fundamentals["fields"]["net_income"]["reasons"])

    def test_scale_conflicts_and_ratios_derived_from_them_are_quarantined(self) -> None:
        normalized = normalize(
            {
                "period": "2025FY",
                "revenue": 38_000_000_000.0,
                "net_income": 2_000_000_000.0,
                "shareholders_equity": 3_000_000.0,
                "roe": 66.67,
                "source_evidence_ids": ["E001"],
                "field_details": {
                    "roe": {"method": "derived", "source_evidence_ids": ["E001"]},
                },
            }
        )

        fundamentals = normalized["fundamentals"]
        self.assertEqual("quarantined", fundamentals["fields"]["shareholders_equity"]["status"])
        self.assertIn("amount_scale_conflict", fundamentals["fields"]["shareholders_equity"]["reasons"])
        self.assertEqual("quarantined", fundamentals["fields"]["roe"]["status"])
        self.assertIn("derived_from_quarantined_field", fundamentals["fields"]["roe"]["reasons"])

    def test_raw_amount_scale_mismatch_and_context_only_usage_are_quarantined(self) -> None:
        normalized = normalize(
            {
                "period": "2026Q1",
                "revenue": 241_832_000_000.0,
                "operating_income": 38_398_000_000.0,
                "source_evidence_ids": ["E001"],
                "field_details": {
                    "revenue": {
                        "raw_value": 82_886.0,
                        "unit": "million USD",
                        "normalized_unit": "CNY",
                        "allowed_usage": "promotion_evidence",
                    },
                    "operating_income": {
                        "raw_value": 38_398.0,
                        "unit": "million CNY",
                        "normalized_unit": "CNY",
                        "allowed_usage": "context_only",
                    },
                },
            }
        )

        fundamentals = normalized["fundamentals"]
        self.assertIn("raw_normalized_value_mismatch", fundamentals["fields"]["revenue"]["reasons"])
        self.assertIn("usage_not_allowed", fundamentals["fields"]["operating_income"]["reasons"])

    def test_secondary_news_is_never_core_evidence(self) -> None:
        normalized = normalize(
            {"period": "2026Q1", "revenue": 100.0, "source_evidence_ids": ["E001"]},
            {
                "items": [
                    {
                        "evidence_id": "E001",
                        "source_type": "news",
                        "source_quality": "secondary",
                        "source_status": "active",
                        "published_at": "2026-07-20",
                        "text_excerpt": "Unrelated market story",
                        "quality_score": 0.95,
                        "usable_for_core_claim": True,
                    }
                ]
            },
        )

        self.assertFalse(normalized["evidence"]["items"][0]["usable_for_core_claim"])

    def test_undated_derived_snapshot_evidence_is_context_only(self) -> None:
        normalized = normalize(
            {"period": "2026Q1", "revenue": 100.0, "source_evidence_ids": ["E001"]},
            {
                "items": [
                    {
                        "evidence_id": "E001",
                        "source_type": "fundamentals",
                        "source_status": "active",
                        "published_at": None,
                        "text_excerpt": "derived snapshot",
                        "quality_score": 0.95,
                        "usable_for_core_claim": True,
                    }
                ]
            },
        )

        item = normalized["evidence"]["items"][0]
        self.assertFalse(item["usable_for_core_claim"])
        self.assertEqual("context_only", item["status"])

    def test_periodless_conflicting_snapshot_is_quarantined(self) -> None:
        normalized = normalize(
            {
                "period": None,
                "revenue": 38_200_000_000,
                "gross_profit": 280_600_000_000,
                "eps_basic": 2025,
                "source_evidence_ids": ["E001"],
            }
        )

        fundamentals = normalized["fundamentals"]
        self.assertEqual("quarantined", fundamentals["status"])
        self.assertEqual("quarantined", fundamentals["fields"]["revenue"]["status"])
        self.assertEqual("quarantined", fundamentals["fields"]["gross_profit"]["status"])
        self.assertEqual("quarantined", fundamentals["fields"]["eps_basic"]["status"])
        self.assertEqual([], fundamentals["valid_fields"])
        self.assertIn("missing_report_period", {issue["code"] for issue in fundamentals["issues"]})

    def test_percentage_ratio_is_normalized_and_keeps_provenance(self) -> None:
        normalized = normalize(
            {
                "period": "2026Q1",
                "revenue": 100.0,
                "gross_profit": 46.06,
                "gross_margin": 46.06,
                "net_income": 12.0,
                "source_evidence_ids": ["E001"],
            }
        )

        gross_margin = normalized["fundamentals"]["fields"]["gross_margin"]
        self.assertEqual("valid", gross_margin["status"])
        self.assertAlmostEqual(0.4606, gross_margin["value"])
        self.assertEqual(["E001"], gross_margin["evidence_ids"])
        self.assertIn("percent_normalized_to_ratio", gross_margin["reasons"])


class StockResearchPacketTests(unittest.TestCase):
    def test_unknown_field_evidence_breaks_closure_and_quarantines_field(self) -> None:
        normalized = normalize(
            {
                "period": "2026Q1",
                "revenue": 100.0,
                "net_income": 12.0,
                "source_evidence_ids": ["E999"],
            },
            evidence("E001"),
        )

        packet = build_stock_research_packet(ticker="300308.SZ", market="A", normalized=normalized)

        self.assertEqual("2.0", packet["schema_version"])
        self.assertEqual("evidence_limited", packet["quality"]["readiness"])
        self.assertIn("evidence_closure_failed", packet["quality"]["blockers"])
        self.assertEqual("quarantined", packet["datasets"]["fundamentals"]["fields"]["revenue"]["status"])
        self.assertIn("fundamentals.revenue", packet["quality"]["quarantined_fields"])

    def test_healthy_packet_is_research_ready(self) -> None:
        normalized = normalize(
            {
                "period": "2026Q1",
                "revenue": 100.0,
                "net_income": 12.0,
                "operating_cash_flow": 18.0,
                "source_evidence_ids": ["E001"],
            }
        )

        packet = build_stock_research_packet(ticker="300308.SZ", market="A", normalized=normalized)

        self.assertEqual("research_ready", packet["quality"]["readiness"])
        self.assertEqual([], packet["quality"]["blockers"])
        self.assertEqual(
            ["revenue", "net_income", "operating_cash_flow"],
            packet["quality"]["valid_core_fundamental_fields"],
        )


if __name__ == "__main__":
    unittest.main()
