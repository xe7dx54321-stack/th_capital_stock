from __future__ import annotations

import unittest

from smr_app.research.claim_compiler import compile_stock_claims, validate_model_rewrites
from smr_app.research.normalization import normalize_research_data
from smr_app.research.quality_gate import evaluate_stock_research_quality
from smr_app.research.report_compiler import compile_stock_research_report, validate_stock_research_report
from smr_app.research.stock_packet import build_stock_research_packet


def make_packet(
    *,
    fundamentals: dict | None = None,
    valuation: dict | None = None,
    evidence_id: str = "E001",
) -> dict:
    normalized = normalize_research_data(
        market="A",
        fundamentals=fundamentals
        if fundamentals is not None
        else {
            "period": "2026Q1",
            "revenue": 100.0,
            "net_income": 12.0,
            "operating_cash_flow": 18.0,
            "gross_margin": 46.0,
            "source_evidence_ids": [evidence_id],
            "field_details": {
                "revenue": {"previous_value": 80.0, "previous_period": "2025Q1"},
            },
        },
        valuation=valuation or {},
        evidence={
            "items": [
                {
                    "evidence_id": evidence_id,
                    "source_key": "official_filing",
                    "source_type": "official_filing",
                    "source_quality": "official",
                    "source_status": "active",
                    "published_at": "2026-07-10",
                    "url_or_doc_id": "doc-1",
                    "text_excerpt": "公司披露本期经营数据。",
                    "quality_score": 0.95,
                    "usable_for_core_claim": True,
                    "metadata": {"claim_category": "fact"},
                }
            ]
        },
        risk={"alerts": []},
        freshness={"status": "fresh", "condition": "current", "blocking_level": "none"},
    )
    return build_stock_research_packet(ticker="300308.SZ", market="A", normalized=normalized)


class StockClaimCompilerTests(unittest.TestCase):
    def test_long_filing_excerpt_is_represented_by_a_concise_source_claim(self) -> None:
        packet = make_packet()
        item = packet["datasets"]["evidence"]["items"][0]
        item["metadata"]["title"] = "2025年年度报告"
        item["text_excerpt"] = "38239935640.67 " * 200

        compiled = compile_stock_claims(packet)
        source_claim = next(
            claim for claim in compiled["claims"] if claim["source_paths"] == ["evidence.E001"]
        )

        self.assertIn("《2025年年度报告》", source_claim["statement"])
        self.assertLess(len(source_claim["statement"]), 220)
        self.assertNotIn("38239935640.67", source_claim["statement"])

    def test_large_currency_values_are_human_readable_and_non_core_noise_is_omitted(self) -> None:
        packet = make_packet(
            fundamentals={
                "period": "2025FY",
                "revenue": 38_239_935_640.67,
                "operating_income": 13_596_919_899.8,
                "cash_and_equivalents": 8_000_000_000.0,
                "source_evidence_ids": ["E001"],
            }
        )

        compiled = compile_stock_claims(packet)
        statements = "\n".join(claim["statement"] for claim in compiled["claims"])

        self.assertIn("382.40 亿人民币", statements)
        self.assertIn("135.97 亿人民币", statements)
        self.assertNotIn("现金及等价物", statements)

    def test_compiler_builds_only_evidence_closed_claims_and_structured_scenarios(self) -> None:
        packet = make_packet()

        compiled = compile_stock_claims(packet)

        usable = set(packet["quality"]["usable_evidence_ids"])
        auditable = [claim for claim in compiled["claims"] if claim["requires_evidence"]]
        self.assertTrue(auditable)
        self.assertTrue(all(set(claim["evidence_ids"]) <= usable for claim in auditable))
        self.assertIn("change", {claim["category"] for claim in auditable})
        self.assertEqual(3, len(compiled["scenarios"]))
        self.assertTrue(all(scenario["conditions"] for scenario in compiled["scenarios"]))
        self.assertTrue(all(scenario["invalidation"] for scenario in compiled["scenarios"]))

    def test_ratio_changes_are_reported_in_percentage_points(self) -> None:
        packet = make_packet(
            fundamentals={
                "period": "2025FY",
                "gross_margin": 0.2746,
                "source_evidence_ids": ["E001"],
                "field_details": {
                    "gross_margin": {
                        "previous_value": 0.3070,
                        "previous_period": "2024FY",
                    },
                },
            }
        )

        compiled = compile_stock_claims(packet)
        statements = "\n".join(claim["statement"] for claim in compiled["claims"])

        self.assertIn("毛利率相较 2024FY 下降 3.24 个百分点", statements)
        self.assertNotIn("毛利率相较 2024FY 下降 10.55%", statements)

    def test_missing_fields_become_questions_not_unsupported_claims(self) -> None:
        packet = make_packet(
            fundamentals={
                "period": None,
                "revenue": 38_200_000_000,
                "gross_profit": 280_600_000_000,
                "source_evidence_ids": ["E001"],
            }
        )

        compiled = compile_stock_claims(packet)

        self.assertFalse(any("38200000000" in claim["statement"] for claim in compiled["claims"]))
        self.assertTrue(compiled["research_questions"])
        self.assertEqual("cannot_conclude", compiled["conclusion_status"])

    def test_model_rewrite_cannot_add_claims_citations_or_forbidden_conclusions(self) -> None:
        packet = make_packet()
        compiled = compile_stock_claims(packet)
        claim = compiled["claims"][0]
        valid_claim = compiled["claims"][1]

        result = validate_model_rewrites(
            packet,
            compiled["claims"],
            [
                {
                    "claim_id": claim["claim_id"],
                    "statement": "建议买入，目标价 200 元。",
                    "evidence_ids": ["E999"],
                },
                {
                    "claim_id": "invented",
                    "statement": "模型新增了一条结论。",
                    "evidence_ids": ["E001"],
                },
                {
                    "claim_id": valid_claim["claim_id"],
                    "statement": "在不改变事实边界的前提下重新表述。",
                    "evidence_ids": valid_claim["evidence_ids"],
                },
            ],
        )

        self.assertEqual(1, len(result["accepted_claims"]))
        self.assertEqual(2, len(result["rejected_rewrites"]))

    def test_cited_valuation_is_only_compiled_as_neutral_point_in_time_fact(self) -> None:
        packet = make_packet(
            valuation={
                "generated_at": "2026-07-10",
                "current_price": 42.0,
                "pe_ttm": 25.0,
                "source_evidence_ids": ["E001"],
                "allowed_usage": "research",
            }
        )

        compiled = compile_stock_claims(packet)
        valuation_claims = [claim for claim in compiled["claims"] if claim["category"] == "valuation"]

        self.assertEqual(2, len(valuation_claims))
        self.assertTrue(all("高估" not in claim["statement"] for claim in valuation_claims))
        self.assertTrue(all("低估" not in claim["statement"] for claim in valuation_claims))
        self.assertTrue(all("目标价" not in claim["statement"] for claim in valuation_claims))


class StockResearchQualityGateTests(unittest.TestCase):
    def test_gate_rejects_quarantined_field_and_forbidden_recommendation(self) -> None:
        packet = make_packet()
        compiled = compile_stock_claims(packet)
        packet["quality"]["quarantined_fields"].append("valuation.current_price")
        packet["claims"] = [
            *compiled["claims"],
            {
                "claim_id": "bad_claim",
                "category": "valuation",
                "claim_type": "valuation",
                "statement": "当前明显低估，建议买入，目标价 200 元。",
                "evidence_ids": ["E001"],
                "source_paths": ["valuation.current_price"],
                "requires_evidence": True,
                "limitations": [],
            },
        ]
        packet["scenarios"] = compiled["scenarios"]
        packet["research_questions"] = compiled["research_questions"]

        gate = evaluate_stock_research_quality(packet)

        self.assertEqual(1, len(gate["rejected_claims"]))
        self.assertNotIn("bad_claim", {claim["claim_id"] for claim in gate["approved_claims"]})
        self.assertIn("forbidden_conclusion", gate["rejected_claims"][0]["reasons"])
        self.assertIn("quarantined_source_field", gate["rejected_claims"][0]["reasons"])

    def test_report_uses_only_approved_claims_and_never_leaks_quarantined_values(self) -> None:
        sentinel = 987_654_321_012
        packet = make_packet(
            fundamentals={
                "period": "2026Q1",
                "revenue": 100.0,
                "net_income": 12.0,
                "gross_profit": sentinel,
                "source_evidence_ids": ["E001"],
            }
        )
        compiled = compile_stock_claims(packet)
        packet["claims"] = compiled["claims"]
        packet["scenarios"] = compiled["scenarios"]
        packet["research_questions"] = compiled["research_questions"]
        gate = evaluate_stock_research_quality(packet)

        report = compile_stock_research_report(packet, gate)

        self.assertNotIn(str(sentinel), report)
        self.assertIn("研究状态", report)
        self.assertIn("证据有限", report)
        self.assertNotIn(gate["report_status"], report)
        self.assertTrue(all(claim["statement"] not in report for claim in gate["rejected_claims"]))
        validation = validate_stock_research_report(report, packet, gate)
        self.assertEqual("passed", validation["status"])

    def test_final_report_validator_rejects_unknown_citations_and_status_drift(self) -> None:
        packet = make_packet()
        compiled = compile_stock_claims(packet)
        packet["claims"] = compiled["claims"]
        packet["scenarios"] = compiled["scenarios"]
        gate = evaluate_stock_research_quality(packet)

        validation = validate_stock_research_report(
            "# 错误报告\n\n- 研究状态：cannot_conclude\n- 编造内容 [E999]\n",
            packet,
            gate,
        )

        self.assertEqual("failed", validation["status"])
        self.assertIn("unknown_report_citation", {error["code"] for error in validation["errors"]})
        self.assertIn("report_status_mismatch", {error["code"] for error in validation["errors"]})

    def test_empty_report_marks_citation_coverage_not_applicable(self) -> None:
        packet = make_packet(fundamentals={})
        packet["quality"]["usable_evidence_ids"] = []
        packet["datasets"]["evidence"]["items"] = []
        compiled = compile_stock_claims(packet)
        packet["claims"] = compiled["claims"]
        packet["scenarios"] = compiled["scenarios"]
        packet["research_questions"] = compiled["research_questions"]
        gate = evaluate_stock_research_quality(packet)

        report = compile_stock_research_report(packet, gate)

        self.assertIsNone(gate["citation_coverage"])
        self.assertIn("引用覆盖率：不适用", report)


if __name__ == "__main__":
    unittest.main()
