#!/usr/bin/env python3
"""Deterministic Bear Case Agent v1 for buy/add candidates."""

from __future__ import annotations

from typing import Any

from smr_claim_graph import _hash_id, ensure_claim_graph_tables, link_claim_evidence, upsert_claim


def build_bear_case(
    conn,
    report_id: str,
    recommendation_id: str | None,
    dashboard_summary: dict[str, Any] | None = None,
    valuation_snapshot: dict[str, Any] | None = None,
    missing_data: list[dict[str, Any]] | list[str] | None = None,
    evidence_ids: list[str] | None = None,
) -> dict[str, Any]:
    ensure_claim_graph_tables(conn)
    summary = dashboard_summary or {}
    valuation = valuation_snapshot or {}
    missing = missing_data or []
    evidence_ids = evidence_ids or []
    action_text = str(summary.get("action_detail") or summary.get("action") or "")
    bear_claims = []
    if valuation.get("allowed_usage") == "context_only" or valuation.get("valuation_status") in {"partial", "stale_price", "missing"}:
        bear_claims.append(
            {
                "claim_text": "估值事实层仍不完整，当前结论不能把估值便宜或赔率充分作为强支撑。",
                "claim_type": "valuation_risk",
                "severity": "medium",
                "what_would_confirm": "补齐 forward EPS、历史分位、同行对比后，估值仍有安全边际。",
            }
        )
    if missing:
        bear_claims.append(
            {
                "claim_text": "关键数据仍有缺口，预期修正、产业链验证或价格有效性可能不足。",
                "claim_type": "missing_data_risk",
                "severity": "medium",
                "what_would_confirm": "缺失数据补齐后仍支持原核心假设。",
            }
        )
    if not bear_claims:
        bear_claims.append(
            {
                "claim_text": "市场可能已经提前反映主线景气变化，后续需要财报、订单或价格行为继续确认。",
                "claim_type": "price_in_risk",
                "severity": "medium",
                "what_would_confirm": "盈利预测或订单证据继续上修，且价格反应未过度透支。",
            }
        )
    deal_breakers = summary.get("kill_triggers") or [
        "主要客户 capex 或订单能见度下修。",
        "毛利率连续两个季度下滑且无法由产品结构解释。",
        "核心证据更新后不再支持原投资假设。",
    ]
    inserted_claim_ids = []
    for index, claim in enumerate(bear_claims, start=1):
        claim_id = _hash_id("claim", report_id, recommendation_id, "bear", index, claim["claim_text"])
        upsert_claim(
            conn,
            {
                "claim_id": claim_id,
                "report_id": report_id,
                "recommendation_id": recommendation_id,
                "ticker": None,
                "theme": summary.get("theme"),
                "claim_text": claim["claim_text"],
                "claim_type": "bear_case",
                "importance": "supporting",
                "stance": "bear",
                "confidence": 0.55,
                "metadata": {**claim, "agent": "bear_case_v1"},
            },
        )
        inserted_claim_ids.append(claim_id)
        for evidence_id in evidence_ids[:2]:
            link_claim_evidence(conn, claim_id, evidence_id, "contextual", 0.45, "Bear Case v1 使用同一证据包作反方复核锚点。")
    adjustment = "reduce_position_or_wait" if action_text else "observe"
    return {
        "bear_case_claims": bear_claims,
        "deal_breakers": deal_breakers,
        "recommendation_adjustment": adjustment,
        "claim_ids": inserted_claim_ids,
    }
