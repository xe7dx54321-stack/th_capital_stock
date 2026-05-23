#!/usr/bin/env python3
"""Field-level financial table extraction for live A/H filing parsing."""

from __future__ import annotations

import re
import sqlite3
from datetime import datetime, timedelta
from typing import Any

from smr_filing_chunk_selector import select_relevant_document_chunks


FIELD_ORDER = [
    "revenue",
    "gross_profit",
    "operating_income",
    "net_income",
    "eps_basic",
    "eps_diluted",
    "operating_cash_flow",
    "capex",
    "free_cash_flow",
    "cash_and_equivalents",
    "total_debt",
    "shareholders_equity",
    "gross_margin",
    "operating_margin",
    "net_margin",
    "roe",
    "roic",
]

FIELD_SYNONYMS: dict[str, list[str]] = {
    "revenue": ["营业收入", "主营业务收入", "营业总收入", "收入", "收益", "营收", "revenue", "net sales", "total revenue", "sales revenue", "operating revenue", "營業收入", "營收"],
    "gross_profit": ["毛利润", "毛利", "毛利额", "gross profit", "毛利總額", "毛利潤"],
    "operating_income": ["营业利润", "经营利润", "income from operations", "operating income", "profit from operations", "经营活动利润", "營業利潤"],
    "net_income": ["净利润", "归母净利润", "归属于母公司股东的净利润", "本公司拥有人应占利润", "net income", "net profit", "profit attributable", "profit attributable to owners", "淨利潤", "純利"],
    "eps_basic": ["基本每股收益", "每股基本收益", "基本每股盈利", "basic eps", "basic earnings per share", "每股收益（基本）", "每股收益-基本"],
    "eps_diluted": ["稀释每股收益", "每股稀释收益", "每股摊薄收益", "diluted eps", "diluted earnings per share", "摊薄每股收益", "每股收益（稀释）"],
    "operating_cash_flow": ["经营活动产生的现金流量净额", "经营现金流", "经营活动现金流", "net cash provided by operating activities", "operating cash flow", "cash flow from operating activities", "營運現金流"],
    "capex": ["购建固定资产、无形资产和其他长期资产支付的现金", "资本开支", "资本性支出", "capital expenditures", "capital expenditure", "capex", "purchase of property plant and equipment", "购置固定资产"],
    "cash_and_equivalents": ["现金及现金等价物", "现金及等价物", "货币资金", "现金及银行结余", "cash and cash equivalents", "cash and bank balances", "cash", "现金及现金等价项", "現金及現金等價物"],
    "total_debt": ["总债务", "债务", "借款", "有息负债", "总借款", "total debt", "borrowings", "interest-bearing borrowings", "long-term debt", "短期借款", "长期借款"],
    "shareholders_equity": ["股东权益", "所有者权益", "归属于母公司股东权益", "equity attributable to owners", "shareholders' equity", "stockholders' equity", "total equity", "本公司擁有人應佔權益"],
}

DEFAULT_CURRENCY_BY_MARKET = {"A": "CNY", "H": "HKD", "US": "USD"}
NUMERIC_RE = re.compile(r"(?<![\w.])-?\(?\d{1,3}(?:,\d{3})*(?:\.\d+)?\)?|-?\d+(?:\.\d+)?")
YEAR_RE = re.compile(r"^20\d{2}$")

UNIT_PATTERNS: list[tuple[re.Pattern[str], float, str]] = [
    (re.compile(r"百万元|million", re.I), 1_000_000.0, "million"),
    (re.compile(r"亿元|billion", re.I), 100_000_000.0, "hundred_million"),
    (re.compile(r"万元|ten\s*thousand", re.I), 10_000.0, "ten_thousand"),
    (re.compile(r"千元|thousand", re.I), 1_000.0, "thousand"),
]


def default_currency_for_market(market: str | None) -> str:
    return DEFAULT_CURRENCY_BY_MARKET.get(str(market or "").upper(), "CNY")


def relation_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name=?", (name,)).fetchone()
    return bool(row)


def normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def parse_dt(value: Any) -> datetime | None:
    text = normalize_text(value)
    if not text:
        return None
    text = text.replace("T", " ")[:19]
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[: len(fmt)], fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def market_for_ticker(ticker: str | None) -> str | None:
    text = str(ticker or "").upper()
    if text.endswith((".SZ", ".SH", ".BJ")):
        return "A"
    if text.endswith(".HK"):
        return "H"
    if text:
        return "US"
    return None


def split_lines(text: str) -> list[str]:
    prepared = re.sub(r"(\[Table_[^\]]+\])", r"\n\1\n", text or "")
    for marker in ("单位：", "单位:", "注："):
        prepared = prepared.replace(marker, f"\n{marker}")
    lines = [normalize_text(line) for line in prepared.splitlines()]
    return [line for line in lines if line]


def detect_unit_context(text: str, market: str | None = None) -> dict[str, Any]:
    lower = normalize_text(text).lower()
    unit_label = ""
    multiplier = 1.0
    for pattern, factor, label in UNIT_PATTERNS:
        if pattern.search(lower):
            unit_label = label
            multiplier = factor
            break
    currency = default_currency_for_market(market)
    if "港" in text or "hkd" in lower:
        currency = "HKD"
    elif "美元" in text or "usd" in lower or re.search(r"(?<![A-Za-z])\$(?!\d)", text or ""):
        currency = "USD"
    elif "人民币" in text or "rmb" in lower or "cny" in lower:
        currency = "CNY"
    if unit_label == "per_share":
        unit = f"{currency}/share"
    elif unit_label:
        unit = f"{unit_label} {currency}"
    else:
        unit = currency
    return {"unit": unit, "currency": currency, "multiplier": multiplier, "unit_label": unit_label}


def _token_value(token: str) -> float | None:
    cleaned = token.strip().replace(",", "")
    if not cleaned:
        return None
    negative = cleaned.startswith("-") or cleaned.startswith("(")
    cleaned = cleaned.strip("()")
    try:
        value = float(cleaned)
    except ValueError:
        return None
    return -abs(value) if negative and value >= 0 else value


def _is_year_like(token: str) -> bool:
    return bool(YEAR_RE.match(token.replace(",", "").strip()))


def _contains_percentage_noise(text: str) -> bool:
    lower = text.lower()
    return any(token in lower for token in ("同比", "环比", "yoy", "mom", "%", "百分比", "增长率", "rate"))


def _field_detail_defaults(field: str, market: str | None, period: str | None, missing_reason: str) -> dict[str, Any]:
    currency = default_currency_for_market(market)
    return {
        "field": field,
        "extracted_value": None,
        "unit": currency,
        "currency": currency,
        "period": period,
        "source_evidence_id": None,
        "source_evidence_ids": [],
        "confidence": 0.0,
        "missing_reason": missing_reason,
        "source_text": "",
        "chunk_id": None,
        "chunk_section_type": None,
        "method": "table_window",
        "warnings": [],
    }


def _score_candidate(field: str, line: str, chunk: dict[str, Any], window: str, token: str, token_index: int, market: str | None, unit_info: dict[str, Any], stale: bool) -> float:
    score = 0.35
    if any(syn.lower() in line.lower() for syn in FIELD_SYNONYMS.get(field, [])):
        score += 0.2
    if token_index <= 40:
        score += 0.15
    if chunk.get("chunk_section_type") in {"financial_statement", "management_discussion", "guidance_outlook", "business_update", "segment_performance", "liquidity_capital"}:
        score += 0.12
    if float(chunk.get("investment_relevance_score") or 0.0) >= 0.6:
        score += 0.08
    if unit_info.get("unit_label"):
        score += 0.1
    if unit_info.get("currency") == default_currency_for_market(market):
        score += 0.05
    if not _contains_percentage_noise(window):
        score += 0.05
    if _is_year_like(token):
        score -= 0.7
    if "%" in token:
        score -= 0.5
    if stale:
        score -= 0.12
    return max(0.0, min(score, 1.0))


def _candidate_from_window(field: str, chunk: dict[str, Any], window: str, line: str, token_match: re.Match[str], market: str | None, stale: bool) -> dict[str, Any] | None:
    token = token_match.group(0)
    raw_value = _token_value(token)
    if raw_value is None:
        return None
    if field not in {"eps_basic", "eps_diluted"}:
        if _is_year_like(token) or "%" in token:
            return None
        if _contains_percentage_noise(window) and not any(marker in window.lower() for marker in ("百万元", "亿元", "万元", "million", "billion", "元", "rmb", "cny", "hkd", "usd")):
            return None
    unit_info = detect_unit_context(window, market)
    value = raw_value
    if field in {"revenue", "gross_profit", "operating_income", "net_income", "operating_cash_flow", "capex", "cash_and_equivalents", "total_debt", "shareholders_equity"}:
        value = abs(value) * float(unit_info.get("multiplier") or 1.0)
    elif field in {"eps_basic", "eps_diluted"}:
        value = value * float(unit_info.get("multiplier") or 1.0)
    confidence = _score_candidate(
        field=field,
        line=line,
        chunk=chunk,
        window=window,
        token=token,
        token_index=token_match.start(),
        market=market,
        unit_info=unit_info,
        stale=stale,
    )
    return {
        "field": field,
        "extracted_value": value,
        "unit": unit_info.get("unit"),
        "currency": unit_info.get("currency"),
        "period": chunk.get("published_at") or chunk.get("ingested_at"),
        "source_evidence_id": chunk.get("evidence_id"),
        "source_evidence_ids": [chunk.get("evidence_id")] if chunk.get("evidence_id") else [],
        "confidence": confidence,
        "missing_reason": None,
        "source_text": window[:320],
        "chunk_id": chunk.get("chunk_id"),
        "chunk_section_type": chunk.get("chunk_section_type"),
        "method": "table_window",
        "warnings": [],
    }


def _best_chunk_for_field(field: str, chunks: list[dict[str, Any]], market: str | None, stale: bool) -> tuple[dict[str, Any] | None, str | None]:
    if field not in FIELD_SYNONYMS:
        return None, "mapping_missing"
    candidates: list[dict[str, Any]] = []
    synonym_seen = False
    parse_failure_seen = False
    for chunk in chunks:
        text = normalize_text(chunk.get("text") or "")
        if not text or not any(syn.lower() in text.lower() for syn in FIELD_SYNONYMS[field]):
            continue
        synonym_seen = True
        lines = split_lines(text) or [text]
        unit_info = detect_unit_context(text, market)
        for index, line in enumerate(lines):
            if not any(syn.lower() in line.lower() for syn in FIELD_SYNONYMS[field]):
                continue
            windows = [line]
            if index + 1 < len(lines):
                windows.append(f"{line} {lines[index + 1]}")
            if index > 0:
                windows.append(f"{lines[index - 1]} {line}")
            if unit_info.get("unit_label"):
                windows.append(f"{line} {text[:160]}")
            found = False
            for window in windows:
                for match in NUMERIC_RE.finditer(window):
                    candidate = _candidate_from_window(field, chunk, window, line, match, market, stale)
                    if candidate is None:
                        continue
                    candidates.append(candidate)
                    found = True
            if not found:
                parse_failure_seen = True
    if not candidates:
        if not synonym_seen:
            return None, "stale_filing" if stale else "field_not_found"
        return None, "parse_failed" if parse_failure_seen else ("stale_filing" if stale else "field_not_found")
    candidates.sort(key=lambda item: (float(item.get("confidence") or 0.0), 1 if item.get("unit") else 0, 1 if item.get("currency") else 0), reverse=True)
    best = candidates[0]
    if len(candidates) > 1:
        second = candidates[1]
        if best.get("unit") != second.get("unit") and abs(float(best.get("confidence") or 0.0) - float(second.get("confidence") or 0.0)) <= 0.12:
            best["warnings"] = list(best.get("warnings") or []) + ["ambiguous_unit"]
            best["confidence"] = round(max(0.0, float(best.get("confidence") or 0.0) - 0.1), 3)
            best["missing_reason"] = "ambiguous_unit"
    return best, None


def _derive_metric(field: str, numerator: dict[str, Any] | None, denominator: dict[str, Any] | None, formula: str) -> dict[str, Any] | None:
    if not numerator or not denominator:
        return None
    num = numerator.get("extracted_value")
    den = denominator.get("extracted_value")
    if num in (None, 0) or den in (None, 0):
        return None
    value = float(num) / float(den)
    evidence_ids = [item for item in [numerator.get("source_evidence_id"), denominator.get("source_evidence_id")] if item]
    return {
        "field": field,
        "extracted_value": value,
        "unit": "ratio",
        "currency": numerator.get("currency") or denominator.get("currency"),
        "period": numerator.get("period") or denominator.get("period"),
        "source_evidence_id": evidence_ids[0] if evidence_ids else None,
        "source_evidence_ids": evidence_ids,
        "confidence": round(min(float(numerator.get("confidence") or 0.0), float(denominator.get("confidence") or 0.0)) * 0.92, 3),
        "missing_reason": None,
        "source_text": formula,
        "chunk_id": numerator.get("chunk_id") or denominator.get("chunk_id"),
        "chunk_section_type": numerator.get("chunk_section_type") or denominator.get("chunk_section_type"),
        "method": "derived",
        "warnings": [],
    }


def _latest_chunk_time(chunks: list[dict[str, Any]]) -> datetime | None:
    anchors = [parse_dt(chunk.get("published_at")) or parse_dt(chunk.get("ingested_at")) for chunk in chunks]
    anchors = [anchor for anchor in anchors if anchor]
    return max(anchors) if anchors else None


def _stale_after(days: int) -> timedelta:
    return timedelta(days=max(1, int(days or 365)))


def extract_field_level_fundamentals(
    conn: sqlite3.Connection,
    ticker: str,
    *,
    market: str | None = None,
    limit: int = 32,
    stale_after_days: int = 365,
) -> dict[str, Any]:
    market = market or market_for_ticker(ticker)
    chunks = select_relevant_document_chunks(conn, ticker=ticker, limit=limit, min_investment_relevance=0.45)
    latest_anchor = _latest_chunk_time(chunks)
    stale = bool(latest_anchor and datetime.now() - latest_anchor > _stale_after(stale_after_days))
    field_details: dict[str, Any] = {}
    field_values: dict[str, Any] = {}
    missing_fields: list[str] = []
    missing_reasons: dict[str, str] = {}
    evidence_ids: list[str] = []

    if not chunks:
        for field in FIELD_ORDER:
            field_details[field] = _field_detail_defaults(field, market, None, "table_not_found")
            missing_fields.append(field)
            missing_reasons[field] = "table_not_found"
        return {
            "field_details": field_details,
            "field_values": field_values,
            "missing_fields": missing_fields,
            "field_missing_reasons": missing_reasons,
            "source_evidence_ids": [],
            "source_quality": "missing",
            "freshness_status": "missing",
            "confidence": 0.0,
            "latest_anchor": None,
            "metadata": {"stale": stale, "chunk_count": 0, "usable_chunk_count": 0},
        }

    for field in FIELD_ORDER:
        candidate, reason = _best_chunk_for_field(field, chunks, market, stale)
        if candidate and candidate.get("extracted_value") is not None:
            field_details[field] = candidate
            field_values[field] = candidate["extracted_value"]
            if candidate.get("source_evidence_id"):
                evidence_ids.append(str(candidate["source_evidence_id"]))
        else:
            field_details[field] = _field_detail_defaults(field, market, latest_anchor.strftime("%Y-%m-%d") if latest_anchor else None, reason or ("stale_filing" if stale else "field_not_found"))
            missing_fields.append(field)
            missing_reasons[field] = field_details[field]["missing_reason"]

    if field_values.get("operating_cash_flow") is not None and field_values.get("capex") is not None:
        derived = _derive_metric("free_cash_flow", field_details["operating_cash_flow"], field_details["capex"], "operating_cash_flow - abs(capex)")
        if derived:
            derived["extracted_value"] = float(field_values["operating_cash_flow"]) - abs(float(field_values["capex"]))
            field_details["free_cash_flow"] = derived
            field_values["free_cash_flow"] = derived["extracted_value"]
            if derived.get("source_evidence_id"):
                evidence_ids.extend(derived.get("source_evidence_ids") or [derived["source_evidence_id"]])

    for field, numerator_field, denominator_field in [
        ("gross_margin", "gross_profit", "revenue"),
        ("operating_margin", "operating_income", "revenue"),
        ("net_margin", "net_income", "revenue"),
        ("roe", "net_income", "shareholders_equity"),
        ("roic", "operating_income", "shareholders_equity"),
    ]:
        derived = _derive_metric(field, field_details.get(numerator_field), field_details.get(denominator_field), f"{numerator_field}/{denominator_field}")
        if derived:
            field_details[field] = derived
            field_values[field] = derived["extracted_value"]
            if derived.get("source_evidence_id"):
                evidence_ids.extend(derived.get("source_evidence_ids") or [derived["source_evidence_id"]])

    evidence_ids = list(dict.fromkeys(item for item in evidence_ids if item))
    present_count = len([field for field in FIELD_ORDER if field_values.get(field) is not None])
    source_quality = "primary" if evidence_ids else "secondary"
    freshness_status = "fresh" if present_count >= 4 and not stale else ("degraded" if present_count >= 1 else ("stale" if stale else "missing"))
    confidence = min(0.95, 0.28 + present_count / max(len(FIELD_ORDER), 1) * 0.62 + (0.05 if evidence_ids else 0.0))
    return {
        "field_details": field_details,
        "field_values": field_values,
        "missing_fields": [field for field in FIELD_ORDER if field_values.get(field) is None],
        "field_missing_reasons": {field: field_details[field].get("missing_reason") for field in FIELD_ORDER if field_values.get(field) is None},
        "source_evidence_ids": evidence_ids,
        "source_quality": source_quality,
        "freshness_status": freshness_status,
        "confidence": round(confidence, 3),
        "latest_anchor": latest_anchor.strftime("%Y-%m-%d %H:%M:%S") if latest_anchor else None,
        "metadata": {
            "chunk_count": len(chunks),
            "usable_chunk_count": sum(1 for chunk in chunks if chunk.get("usable_for_core_claim") or chunk.get("usable_for_proxy_signal")),
            "stale": stale,
            "market": market,
        },
    }

