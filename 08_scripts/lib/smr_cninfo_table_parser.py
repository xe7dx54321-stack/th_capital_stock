#!/usr/bin/env python3
"""CNINFO income-statement parser helpers for Phase 16 recovery."""

from __future__ import annotations

import re
from typing import Any


INCOME_STATEMENT_TITLES = [
    "合并利润表",
    "利润表",
    "合并损益表",
    "损益表",
    "consolidated income statement",
    "income statement",
    "consolidated statement of profit or loss",
    "营业收入表",
    "主要会计数据和财务指标",
]

PARENT_COMPANY_MARKERS = ["母公司利润表", "母公司损益表", "parent company income statement"]

REVENUE_SYNONYMS = [
    "营业收入",
    "营业总收入",
    "主营业务收入",
    "收入",
    "销售收入",
    "产品销售收入",
    "客户合同产生的收入",
    "revenue",
    "total revenue",
    "operating revenue",
    "net sales",
    "sales",
]

GROSS_PROFIT_SYNONYMS = ["毛利", "毛利润", "毛利额", "gross profit"]

OPERATING_COST_SYNONYMS = [
    "营业成本",
    "主营业务成本",
    "销售成本",
    "产品销售成本",
    "cost of revenue",
    "cost of sales",
    "operating cost",
]

NUMERIC_RE = re.compile(r"(?<![\d.])-?\(?\d{1,3}(?:,\d{3})*(?:\.\d+)?\)?|-?\d+(?:\.\d+)?")


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _contains_any(text: str, terms: list[str]) -> bool:
    lower = text.lower()
    return any(term.lower() in lower for term in terms)


def _unit_context(text: str) -> dict[str, Any]:
    lower = text.lower()
    scale = 1.0
    unit_label = ""
    if "百万元" in text or "百萬" in text or "million" in lower:
        scale = 1_000_000.0
        unit_label = "million"
    elif "万元" in text or "萬元" in text or "ten thousand" in lower:
        scale = 10_000.0
        unit_label = "ten_thousand"
    elif "亿元" in text or "億元" in text:
        scale = 100_000_000.0
        unit_label = "hundred_million"
    elif "千元" in text or "thousand" in lower:
        scale = 1_000.0
        unit_label = "thousand"
    currency = "CNY"
    if "usd" in lower or "us$" in lower or "美元" in text:
        currency = "USD"
    elif "hkd" in lower or "港币" in text or "港幣" in text:
        currency = "HKD"
    unit = f"{unit_label} {currency}" if unit_label else currency
    return {"unit": unit, "currency": currency, "scale": scale, "unit_label": unit_label}


def _numeric_value(line: str, scale: float) -> float | None:
    if "%" in line or "百分比" in line or "毛利率" in line:
        return None
    matches = [m.group(0) for m in NUMERIC_RE.finditer(line)]
    matches = [m for m in matches if not re.fullmatch(r"20\d{2}", m.replace(",", ""))]
    if not matches:
        return None
    token = matches[-1]
    negative = token.startswith("-") or token.startswith("(")
    cleaned = token.replace(",", "").strip("()")
    try:
        value = float(cleaned)
    except ValueError:
        return None
    if negative:
        value = -abs(value)
    return value * scale


def detect_income_statement_section(text: str) -> dict[str, Any]:
    clean = _clean(text)
    lower = clean.lower()
    matches = [title for title in INCOME_STATEMENT_TITLES if title.lower() in lower]
    parent = any(marker.lower() in lower for marker in PARENT_COMPANY_MARKERS)
    consolidated = any(token in lower for token in ("合并利润表", "合并损益表", "consolidated"))
    scope = "consolidated" if consolidated else ("parent_company" if parent else ("metrics_summary" if "主要会计数据和财务指标" in clean else None))
    return {
        "table_detected": bool(matches),
        "section_type": "income_statement" if matches else None,
        "matched_titles": matches,
        "scope": scope,
    }


def _line_has_field(line: str, synonyms: list[str]) -> bool:
    if _contains_any(line, synonyms):
        return True
    return False


def _extract_field(text: str, field: str, synonyms: list[str], unit: dict[str, Any], *, source_evidence_id: str | None, source_chunk_id: str | None, period: str | None, scope: str | None) -> dict[str, Any] | None:
    for raw_line in str(text or "").splitlines():
        line = _clean(raw_line)
        if not line or not _line_has_field(line, synonyms):
            continue
        if field == "revenue" and _contains_any(line, OPERATING_COST_SYNONYMS):
            continue
        value = _numeric_value(line, float(unit["scale"]))
        if value is None:
            continue
        confidence = 0.82 if scope == "consolidated" else (0.68 if scope == "metrics_summary" else 0.55)
        allowed_usage = "supporting_evidence" if source_evidence_id and confidence >= 0.6 else "context_only"
        if scope == "parent_company":
            allowed_usage = "context_only"
        return {
            "field": field,
            "status": "extracted",
            "value": value,
            "extracted_value": value,
            "unit": unit["unit"],
            "currency": unit["currency"],
            "period": period,
            "source_evidence_id": source_evidence_id,
            "source_evidence_ids": [source_evidence_id] if source_evidence_id else [],
            "source_chunk_id": source_chunk_id,
            "chunk_id": source_chunk_id,
            "source_section_type": "income_statement",
            "chunk_section_type": "income_statement",
            "source_text": line,
            "confidence": confidence,
            "allowed_usage": allowed_usage,
            "missing_reason": None if source_evidence_id else "source_evidence_missing",
            "scope": scope,
            "method": "cninfo_income_statement",
        }
    return None


def derive_gross_profit_from_inputs(revenue: dict[str, Any] | None, operating_cost: dict[str, Any] | None) -> dict[str, Any] | None:
    if not revenue or not operating_cost:
        return None
    if revenue.get("value") is None or operating_cost.get("value") is None:
        return None
    if revenue.get("currency") != operating_cost.get("currency"):
        return None
    evidence_ids = [item for item in [revenue.get("source_evidence_id"), operating_cost.get("source_evidence_id")] if item]
    if len(evidence_ids) < 2:
        return None
    value = float(revenue["value"]) - float(operating_cost["value"])
    confidence = round(min(float(revenue.get("confidence") or 0.0), float(operating_cost.get("confidence") or 0.0)) * 0.92, 3)
    return {
        "field": "gross_profit",
        "status": "derived",
        "value": value,
        "extracted_value": value,
        "formula": "revenue - operating_cost",
        "input_fields": ["revenue", "operating_cost"],
        "input_evidence_ids": evidence_ids,
        "source_evidence_id": evidence_ids[0],
        "source_evidence_ids": evidence_ids,
        "unit": revenue.get("unit"),
        "currency": revenue.get("currency"),
        "period": revenue.get("period"),
        "confidence": confidence,
        "allowed_usage": "supporting_evidence" if confidence >= 0.6 else "context_only",
        "missing_reason": None,
        "source_text": "gross_profit = revenue - operating_cost",
        "source_section_type": "income_statement",
        "chunk_section_type": "income_statement",
        "method": "derived",
        "extraction_method": "derived",
        "scope": revenue.get("scope"),
    }


def extract_income_statement_fields_from_text(
    text: str,
    *,
    ticker: str | None = None,
    source_evidence_id: str | None = None,
    source_chunk_id: str | None = None,
    period: str | None = None,
) -> dict[str, Any]:
    section = detect_income_statement_section(text)
    if not section["table_detected"]:
        return {
            "ticker": ticker,
            "status": "missing",
            "missing_reason": "income_statement_table_not_found",
            "table_detected": False,
            "section_type": None,
            "field_status": {
                "revenue": {"status": "missing", "missing_reason": "income_statement_table_not_found"},
                "gross_profit": {"status": "missing", "missing_reason": "income_statement_table_not_found"},
            },
        }
    unit = _unit_context(text)
    scope = section.get("scope") or "unknown"
    revenue = _extract_field(text, "revenue", REVENUE_SYNONYMS, unit, source_evidence_id=source_evidence_id, source_chunk_id=source_chunk_id, period=period, scope=scope)
    operating_cost = _extract_field(text, "operating_cost", OPERATING_COST_SYNONYMS, unit, source_evidence_id=source_evidence_id, source_chunk_id=source_chunk_id, period=period, scope=scope)
    gross_profit = _extract_field(text, "gross_profit", GROSS_PROFIT_SYNONYMS, unit, source_evidence_id=source_evidence_id, source_chunk_id=source_chunk_id, period=period, scope=scope)
    if not gross_profit:
        gross_profit = derive_gross_profit_from_inputs(revenue, operating_cost)
    field_status = {
        "revenue": revenue or {"field": "revenue", "status": "missing", "missing_reason": "revenue_field_not_found", "scope": scope},
        "operating_cost": operating_cost or {"field": "operating_cost", "status": "missing", "missing_reason": "operating_cost_field_not_found", "scope": scope},
        "gross_profit": gross_profit
        or {
            "field": "gross_profit",
            "status": "missing",
            "missing_reason": "derived_field_missing_inputs",
            "missing_inputs": [name for name, item in [("revenue", revenue), ("operating_cost", operating_cost)] if not item],
            "scope": scope,
        },
    }
    return {
        "ticker": ticker,
        "status": "parsed",
        "missing_reason": None,
        "table_detected": True,
        "section_type": "income_statement",
        "scope": scope,
        "field_status": field_status,
    }


def extract_income_statement_fields_from_chunks(chunks: list[dict[str, Any]], *, ticker: str) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for chunk in chunks:
        result = extract_income_statement_fields_from_text(
            str(chunk.get("text") or ""),
            ticker=ticker,
            source_evidence_id=chunk.get("evidence_id"),
            source_chunk_id=chunk.get("chunk_id"),
            period=chunk.get("published_at") or chunk.get("ingested_at"),
        )
        if result.get("table_detected"):
            results.append(result)
    if not results:
        return extract_income_statement_fields_from_text("", ticker=ticker)
    results.sort(
        key=lambda item: (
            3 if item.get("scope") == "consolidated" else 2 if item.get("scope") == "metrics_summary" else 1,
            sum(1 for field in ("revenue", "gross_profit") if (item.get("field_status") or {}).get(field, {}).get("status") in {"extracted", "derived"}),
        ),
        reverse=True,
    )
    return results[0]
