#!/usr/bin/env python3
"""HKEX balance-sheet parser helpers for Phase 16 recovery."""

from __future__ import annotations

import re
from typing import Any


BALANCE_SHEET_TITLES = [
    "consolidated statement of financial position",
    "consolidated balance sheet",
    "statement of financial position",
    "balance sheet",
    "condensed consolidated statement of financial position",
    "簡明綜合財務狀況表",
    "綜合財務狀況表",
    "綜合資產負債表",
    "資產負債表",
    "财务状况表",
    "资产负债表",
]

OWNER_EQUITY_SYNONYMS = [
    "equity attributable to owners",
    "equity attributable to equity holders",
    "equity attributable to shareholders",
    "equity attributable to owners of the company",
    "equity attributable to equity holders of the company",
    "total shareholders' equity",
    "shareholders' equity",
    "equity holders' funds",
    "本公司權益持有人應佔權益",
    "本公司权益持有人应占权益",
    "本公司擁有人應佔權益",
    "本公司拥有人应占权益",
    "股東權益",
    "股东权益",
    "歸屬於母公司股東權益",
    "归属于母公司股东权益",
    "所有者權益合計",
    "所有者权益合计",
]

FALLBACK_EQUITY_SYNONYMS = [
    "total equity",
    "權益總額",
    "权益总额",
    "net assets",
    "淨資產",
    "净资产",
]

NON_CONTROLLING_TERMS = [
    "non-controlling interests",
    "non controlling interests",
    "minority interests",
    "非控股權益",
    "非控股权益",
    "少數股東權益",
    "少数股东权益",
]

NUMERIC_RE = re.compile(r"(?<![\d.])-?\(?\d{1,3}(?:,\d{3})*(?:\.\d+)?\)?|-?\d+(?:\.\d+)?")


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _contains_any(text: str, terms: list[str]) -> bool:
    lower = text.lower()
    return any(term.lower() in lower for term in terms)


def detect_balance_sheet_section(text: str) -> dict[str, Any]:
    clean = _clean(text)
    lower = clean.lower()
    matches = [title for title in BALANCE_SHEET_TITLES if title.lower() in lower]
    return {
        "table_detected": bool(matches),
        "section_type": "balance_sheet" if matches else None,
        "matched_titles": matches,
    }


def _unit_context(text: str, market: str = "H") -> dict[str, Any]:
    lower = text.lower()
    scale = 1.0
    unit_label = ""
    if any(token in lower for token in ("rmb million", "hkd million", "us$ million", "usd million", "million")) or any(
        token in text for token in ("人民幣百萬元", "人民币百万元", "港幣百萬元", "港币百万元", "百萬元", "百万元")
    ):
        scale = 1_000_000.0
        unit_label = "million"
    elif any(token in text for token in ("萬元", "万元")):
        scale = 10_000.0
        unit_label = "ten_thousand"
    elif any(token in text for token in ("億元", "亿元")):
        scale = 100_000_000.0
        unit_label = "hundred_million"
    currency = "HKD" if market == "H" else "CNY"
    if any(token in lower for token in ("rmb", "cny")) or any(token in text for token in ("人民幣", "人民币")):
        currency = "CNY"
    elif "usd" in lower or "us$" in lower or "美元" in text:
        currency = "USD"
    elif "hkd" in lower or any(token in text for token in ("港幣", "港币")):
        currency = "HKD"
    unit = f"{unit_label} {currency}" if unit_label else currency
    return {"unit": unit, "currency": currency, "scale": scale, "unit_label": unit_label}


def _numeric_value(line: str, scale: float) -> float | None:
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


def _candidate_lines(text: str) -> list[tuple[int, str]]:
    return [(index, _clean(line)) for index, line in enumerate(str(text or "").splitlines()) if _clean(line)]


def extract_shareholders_equity_from_text(
    text: str,
    *,
    ticker: str | None = None,
    market: str = "H",
    source_evidence_id: str | None = None,
    source_filing_id: str | None = None,
    source_chunk_id: str | None = None,
    period: str | None = None,
) -> dict[str, Any]:
    section = detect_balance_sheet_section(text)
    if not section["table_detected"]:
        return {
            "field": "shareholders_equity",
            "status": "missing",
            "missing_reason": "balance_sheet_not_found",
            "table_detected": False,
            "section_type": None,
            "confidence": 0.0,
            "allowed_usage": "blocked",
            "ticker": ticker,
        }

    unit = _unit_context(text, market)
    candidates: list[dict[str, Any]] = []
    for index, line in _candidate_lines(text):
        if _contains_any(line, NON_CONTROLLING_TERMS):
            continue
        priority = 0
        fallback_used = False
        if _contains_any(line, OWNER_EQUITY_SYNONYMS):
            priority = 3
        elif _contains_any(line, FALLBACK_EQUITY_SYNONYMS):
            priority = 2
            fallback_used = True
        if not priority:
            continue
        value = _numeric_value(line, float(unit["scale"]))
        if value is None:
            continue
        confidence = 0.82 if priority == 3 else 0.66
        candidates.append(
            {
                "field": "shareholders_equity",
                "status": "extracted",
                "value": value,
                "extracted_value": value,
                "unit": unit["unit"],
                "currency": unit["currency"],
                "period": period,
                "source_evidence_id": source_evidence_id,
                "source_evidence_ids": [source_evidence_id] if source_evidence_id else [],
                "source_filing_id": source_filing_id,
                "source_chunk_id": source_chunk_id,
                "chunk_id": source_chunk_id,
                "source_section_type": "balance_sheet",
                "chunk_section_type": "balance_sheet",
                "source_text": line,
                "confidence": confidence,
                "allowed_usage": "supporting_evidence" if source_evidence_id and confidence >= 0.6 else "blocked",
                "missing_reason": None if source_evidence_id else "source_evidence_missing",
                "fallback_used": fallback_used,
                "method": "hkex_balance_sheet",
                "priority": priority,
                "ticker": ticker,
            }
        )

    if not candidates:
        return {
            "field": "shareholders_equity",
            "status": "missing",
            "missing_reason": "equity_field_not_found",
            "table_detected": True,
            "section_type": "balance_sheet",
            "confidence": 0.0,
            "allowed_usage": "blocked",
            "suggested_fix": "extend equity synonym coverage for HKEX balance sheet",
            "ticker": ticker,
        }

    candidates.sort(key=lambda item: (item["priority"], item["confidence"]), reverse=True)
    best_priority = candidates[0]["priority"]
    top = [item for item in candidates if item["priority"] == best_priority]
    distinct_values = {round(float(item["value"]), 2) for item in top}
    if len(top) > 1 and len(distinct_values) > 1 and best_priority < 3:
        return {
            "field": "shareholders_equity",
            "status": "missing",
            "missing_reason": "ambiguous_equity_field",
            "table_detected": True,
            "section_type": "balance_sheet",
            "candidates": top[:4],
            "confidence": 0.0,
            "allowed_usage": "blocked",
            "ticker": ticker,
        }
    return top[0]


def extract_shareholders_equity_from_chunks(chunks: list[dict[str, Any]], *, ticker: str, market: str = "H") -> dict[str, Any]:
    best_missing: dict[str, Any] | None = None
    for chunk in chunks:
        result = extract_shareholders_equity_from_text(
            str(chunk.get("text") or ""),
            ticker=ticker,
            market=market,
            source_evidence_id=chunk.get("evidence_id"),
            source_filing_id=chunk.get("document_id") or chunk.get("filing_id"),
            source_chunk_id=chunk.get("chunk_id"),
            period=chunk.get("published_at") or chunk.get("ingested_at"),
        )
        if result.get("status") == "extracted" and not result.get("missing_reason"):
            return result
        if result.get("table_detected"):
            best_missing = result
    return best_missing or {
        "field": "shareholders_equity",
        "status": "missing",
        "missing_reason": "balance_sheet_not_found",
        "table_detected": False,
        "section_type": None,
        "confidence": 0.0,
        "allowed_usage": "blocked",
        "ticker": ticker,
    }
