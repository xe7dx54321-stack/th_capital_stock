#!/usr/bin/env python3
"""Phase 27 mock/LLM semantic extractor for IR materials."""

from __future__ import annotations

import re
from typing import Any

from smr_semantic_evidence_schema import make_semantic_extraction, validate_semantic_extraction


PROMPT_GUARDRAILS = """You can only extract from the provided text.
Do not use external knowledge.
Do not infer customer names that are not present.
Do not rewrite "North American customer" as NVIDIA.
Do not rewrite strong demand as confirmed order.
Do not rewrite product mix optimization as ASP increase unless the text explicitly says price/ASP increased.
Return no_extraction when there is no grounded evidence.
Every extraction must include quoted_span copied from the chunk."""


def _sentence_with(text: str, terms: tuple[str, ...]) -> str:
    sentences = [part.strip() for part in re.split(r"(?<=[。.!?？])", text) if part.strip()]
    for sentence in sentences:
        lower = sentence.lower()
        if any(term.lower() in lower for term in terms):
            return sentence
    return ""


def _numbers(span: str) -> list[str]:
    return re.findall(r"\d+(?:\.\d+)?%?|\d+g|\d+t", span, flags=re.IGNORECASE)


def _extract_from_chunk(chunk: dict[str, Any], variable_hint: str) -> dict[str, Any] | None:
    text = str(chunk.get("text") or "")
    ticker = str(chunk.get("ticker") or "")
    source_type = str(chunk.get("source_type") or "unknown")
    source_id = str(chunk.get("source_id") or "")
    chunk_id = str(chunk.get("chunk_id") or "")
    theme = "ai_optical_interconnect"
    mapping = {
        "product_exposure": (("光器件", "光模块", "产品应用", "optical"), "product_exposure", "management_commentary"),
        "capacity_signal": (("产能", "扩产", "建设", "capacity"), "capacity_signal", "management_commentary"),
        "shipment_signal": (("出货", "交付", "shipment"), "shipment_signal", "management_commentary"),
        "ASP_price_signal": (("asp", "单价", "价格", "产品结构"), "ASP_price_signal", "context_only"),
        "margin_signal": (("毛利", "margin"), "margin_signal", "management_commentary"),
        "customer_allocation_signal": (("客户 allocation", "客户分配", "供应份额", "北美客户", "nvidia"), "customer_allocation_signal", "weak"),
        "order_visibility_signal": (("订单", "合同", "需求增长", "需求旺盛"), "order_visibility_signal", "management_commentary"),
        "end_demand_signal": (("需求", "ai 数据中心", "算力"), "end_demand_signal", "proxy_indication"),
        "risk_signal": (("未披露", "不确定", "不构成确认订单"), "risk_signal", "context_only"),
    }
    terms, variable_type, strength = mapping.get(variable_hint, ((), "unknown", "unusable"))
    span = _sentence_with(text, terms)
    if not span:
        return None
    risk_flags = []
    limitations = []
    if "未披露" in span or "不构成确认订单" in span:
        risk_flags.append("not_disclosed")
    if strength == "management_commentary":
        risk_flags.append("management_commentary")
        limitations.append("management commentary, not audited direct evidence")
    if variable_type == "ASP_price_signal" and ("asp" not in span.lower() and "单价" not in span and "价格" not in span):
        risk_flags.append("no_explicit_ASP")
        limitations.append("product mix context is not explicit ASP disclosure")
    if variable_type == "customer_allocation_signal":
        risk_flags.append("no_customer_allocation")
        limitations.append("no explicit customer allocation disclosure")
    nums = _numbers(span)
    return make_semantic_extraction(
        ticker=ticker,
        theme=theme,
        source_id=source_id,
        chunk_id=chunk_id,
        source_type=source_type,
        variable_type=variable_type,
        claim_text=span,
        quoted_span=span,
        direction="negative" if variable_type == "risk_signal" else "positive",
        evidence_strength=strength,
        confidence="medium" if strength in {"management_commentary", "proxy_indication"} else "low",
        is_company_specific=source_type != "industry_public_commentary",
        is_customer_specific=False,
        is_quantified=bool(nums),
        numeric_values=nums,
        customer_names=[],
        product_mentions=[term for term in ("高速光器件", "800G 光模块", "光模块", "光器件") if term in span],
        risk_flags=risk_flags,
        limitations=limitations,
    )


def extract_semantic_evidence(candidates: list[dict[str, Any]], *, mode: str = "mock") -> dict[str, Any]:
    if mode == "llm":
        return {
            "semantic_extractions": [],
            "no_extraction_chunks": [item.get("chunk_id") for item in candidates],
            "llm_enabled": False,
            "prompt_guardrails": PROMPT_GUARDRAILS,
            "message": "LLM mode is reserved and disabled by default; use --mock for deterministic extraction.",
        }
    extractions = []
    no_extraction = []
    for candidate in candidates:
        chunk = candidate.get("chunk") or {}
        extracted_for_chunk = False
        for hint in candidate.get("variables_hint") or []:
            item = _extract_from_chunk(chunk, hint)
            if not item:
                continue
            issues = validate_semantic_extraction(item, chunk_text=str(chunk.get("text") or ""))
            if any(issue.get("severity") == "error" for issue in issues):
                continue
            extractions.append(item)
            extracted_for_chunk = True
        if not extracted_for_chunk:
            no_extraction.append(candidate.get("chunk_id"))
    return {
        "semantic_extractions": extractions,
        "no_extraction_chunks": list(dict.fromkeys(no_extraction)),
        "llm_enabled": False,
        "prompt_guardrails": PROMPT_GUARDRAILS,
    }
