#!/usr/bin/env python3
"""Phase 27 candidate retrieval for semantic extraction.

Keyword matching is only used for recall. The returned variable hints are not
final evidence judgements and must be passed to the semantic extractor/gate.
"""

from __future__ import annotations

from typing import Any


HINT_TERMS = {
    "product_exposure": ("光器件", "光模块", "800g", "1.6t", "产品", "optical", "module"),
    "capacity_signal": ("产能", "扩产", "建设", "capex", "capacity", "ramp"),
    "shipment_signal": ("出货", "交付", "shipment", "delivery"),
    "ASP_price_signal": ("asp", "单价", "价格", "产品结构", "price"),
    "margin_signal": ("毛利", "margin"),
    "customer_allocation_signal": ("客户 allocation", "客户分配", "供应份额", "北美客户", "nvidia", "hyperscaler"),
    "order_visibility_signal": ("订单", "合同", "需求增长", "需求旺盛", "order"),
    "end_demand_signal": ("ai 数据中心", "算力", "需求", "800g", "网络升级"),
    "industry_forecast_signal": ("预测", "forecast", "2025", "2026", "增长"),
    "risk_signal": ("风险", "不确定", "未披露", "未确认"),
}


def retrieve_candidate_chunks(chunks: list[dict[str, Any]], *, min_score: float = 0.15) -> dict[str, Any]:
    candidates = []
    for chunk in chunks:
        text = str(chunk.get("text") or "").lower()
        variables = []
        reasons = []
        hits = 0
        for variable, terms in HINT_TERMS.items():
            matched = [term for term in terms if term.lower() in text]
            if matched:
                variables.append(variable)
                reasons.append(f"contains_{variable}_hint")
                hits += len(matched)
        if not variables:
            continue
        score = min(0.95, 0.1 + hits * 0.08)
        if score < min_score:
            continue
        candidates.append(
            {
                "ticker": chunk.get("ticker"),
                "chunk_id": chunk.get("chunk_id"),
                "source_id": chunk.get("source_id"),
                "candidate_reason": list(dict.fromkeys(reasons)),
                "retrieval_score": round(score, 2),
                "variables_hint": list(dict.fromkeys(variables)),
                "chunk": chunk,
                "final_variable_type": None,
                "evidence_status": None,
            }
        )
    return {
        "ticker": (chunks[0].get("ticker") if chunks else None),
        "candidate_chunks": candidates,
        "no_candidate_chunks": len(candidates) == 0,
        "retriever_only": True,
    }
