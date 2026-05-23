#!/usr/bin/env python3
"""Ticker-level fundamentals snapshot v1."""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime
from typing import Any

from smr_claim_graph import ensure_claim_graph_tables, upsert_evidence
from smr_filing_chunk_selector import select_relevant_document_chunks
from smr_financial_table_extraction import FIELD_ORDER, default_currency_for_market, extract_field_level_fundamentals
from smr_wiki import generate_execution_id, now_ts


FUNDAMENTAL_FIELDS = [
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


def ensure_fundamentals_tables(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS fundamentals_snapshot (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id TEXT UNIQUE NOT NULL,
            ticker TEXT NOT NULL,
            market TEXT,
            period TEXT,
            fiscal_year INTEGER,
            fiscal_quarter TEXT,
            revenue REAL,
            gross_profit REAL,
            operating_income REAL,
            net_income REAL,
            eps_basic REAL,
            eps_diluted REAL,
            operating_cash_flow REAL,
            capex REAL,
            free_cash_flow REAL,
            cash_and_equivalents REAL,
            total_debt REAL,
            shareholders_equity REAL,
            gross_margin REAL,
            operating_margin REAL,
            net_margin REAL,
            roe REAL,
            roic REAL,
            source_evidence_ids_json TEXT NOT NULL DEFAULT '[]',
            source_quality TEXT,
            freshness_status TEXT,
            confidence REAL,
            missing_fields_json TEXT NOT NULL DEFAULT '[]',
            field_details_json TEXT NOT NULL DEFAULT '{}',
            field_missing_reasons_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL,
            metadata_json TEXT NOT NULL DEFAULT '{}'
        );

        CREATE INDEX IF NOT EXISTS idx_fundamentals_snapshot_ticker
        ON fundamentals_snapshot(ticker, created_at DESC);
        """
    )
    columns = {row[1] for row in conn.execute("PRAGMA table_info(fundamentals_snapshot)").fetchall()}
    additions = {
        "field_details_json": "TEXT NOT NULL DEFAULT '{}'",
        "field_missing_reasons_json": "TEXT NOT NULL DEFAULT '{}'",
    }
    for column, ddl in additions.items():
        if column not in columns:
            conn.execute(f"ALTER TABLE fundamentals_snapshot ADD COLUMN {column} {ddl}")


def relation_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name=?", (name,)).fetchone()
    return bool(row)


def table_columns(conn: sqlite3.Connection, name: str) -> set[str]:
    if not relation_exists(conn, name):
        return set()
    return {row[1] for row in conn.execute(f"PRAGMA table_info({name})").fetchall()}


def loads_json(raw: str | None, fallback: Any) -> Any:
    if raw in (None, ""):
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def market_for_ticker(ticker: str | None) -> str | None:
    text = str(ticker or "").upper()
    if text.endswith((".SZ", ".SH", ".BJ")):
        return "A"
    if text.endswith(".HK"):
        return "H"
    if text:
        return "US"
    return None


def normalize_numeric(value: Any) -> float | None:
    if value in (None, "", "None", "-", "--", "nan"):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace(",", "").replace("%", "").strip()
    multiplier = 1.0
    if text.lower().endswith("million"):
        multiplier = 1e6
        text = text[:-7].strip()
    elif text.lower().endswith("billion"):
        multiplier = 1e9
        text = text[:-7].strip()
    try:
        return float(text) * multiplier
    except ValueError:
        return None


def factor_value(conn: sqlite3.Connection, ticker: str, names: list[str]) -> float | None:
    if not relation_exists(conn, "factor_daily"):
        return None
    columns = table_columns(conn, "factor_daily")
    if {"factor_name", "factor_value", "trade_date", "ts_code"}.issubset(columns):
        placeholders = ",".join("?" for _ in names)
        row = conn.execute(
            f"""
            SELECT factor_value
            FROM factor_daily
            WHERE ts_code=? AND factor_name IN ({placeholders})
            ORDER BY trade_date DESC
            LIMIT 1
            """,
            (ticker, *names),
        ).fetchone()
        return normalize_numeric(row[0]) if row else None
    return None


def latest_factor_date(conn: sqlite3.Connection, ticker: str) -> str | None:
    if not relation_exists(conn, "factor_daily"):
        return None
    columns = table_columns(conn, "factor_daily")
    if {"trade_date", "ts_code"}.issubset(columns):
        row = conn.execute("SELECT MAX(trade_date) FROM factor_daily WHERE ts_code=?", (ticker,)).fetchone()
        return row[0] if row else None
    return None


def latest_filing_evidence_ids(conn: sqlite3.Connection, ticker: str, limit: int = 6) -> list[str]:
    if not relation_exists(conn, "evidence_items"):
        return []
    rows = conn.execute(
        """
        SELECT evidence_id
        FROM evidence_items
        WHERE source_type='filing'
          AND (metadata_json LIKE ? OR text_excerpt LIKE ?)
        ORDER BY datetime(COALESCE(published_at, ingested_at, created_at)) DESC, id DESC
        LIMIT ?
        """,
        (f"%{ticker}%", f"%{ticker}%", limit),
    ).fetchall()
    return [row[0] for row in rows]


def sec_companyfacts_url(cik: int) -> str:
    return f"https://data.sec.gov/api/xbrl/companyfacts/CIK{int(cik):010d}.json"


def fetch_sec_companyfacts(symbol: str, timeout: int = 30) -> tuple[dict[str, Any], dict[str, Any] | None]:
    from smr_official_intel import DEFAULT_SEC_USER_AGENT, fetch_url, sec_company_lookup

    meta = sec_company_lookup(symbol, timeout=timeout, user_agent=DEFAULT_SEC_USER_AGENT)
    if not meta:
        return {}, None
    response = fetch_url(
        sec_companyfacts_url(meta["cik"]),
        timeout=timeout,
        user_agent=DEFAULT_SEC_USER_AGENT,
        accept="application/json, text/plain, */*",
    )
    return json.loads(response["text"] or "{}"), meta


def unit_values(companyfacts: dict[str, Any], concept: str) -> list[dict[str, Any]]:
    facts = ((companyfacts.get("facts") or {}).get("us-gaap") or {}).get(concept) or {}
    units = facts.get("units") or {}
    rows: list[dict[str, Any]] = []
    for unit, values in units.items():
        for item in values or []:
            if item.get("val") is None:
                continue
            rows.append({**item, "unit": unit, "concept": concept})
    rows.sort(key=lambda item: (str(item.get("end") or ""), str(item.get("filed") or "")), reverse=True)
    return rows


def latest_fact(companyfacts: dict[str, Any], concepts: list[str], preferred_units: set[str] | None = None) -> tuple[float | None, dict[str, Any] | None]:
    preferred_units = preferred_units or {"USD", "USD/shares", "shares", "pure"}
    for concept in concepts:
        rows = unit_values(companyfacts, concept)
        preferred = [row for row in rows if row.get("unit") in preferred_units]
        for row in preferred or rows:
            value = normalize_numeric(row.get("val"))
            if value is not None:
                return value, row
    return None, None


def same_fact_period(left: dict[str, Any] | None, right: dict[str, Any] | None) -> bool:
    if not left or not right:
        return False
    return bool(left.get("end") and left.get("end") == right.get("end"))


def latest_source_period(source_rows: dict[str, dict[str, Any]]) -> dict[str, Any]:
    rows = [row for row in source_rows.values() if row]
    if not rows:
        return {}
    return sorted(rows, key=lambda item: (str(item.get("end") or ""), str(item.get("filed") or "")), reverse=True)[0]


def build_us_fundamentals(symbol: str, timeout: int = 30) -> tuple[dict[str, Any], dict[str, Any]]:
    companyfacts, meta = fetch_sec_companyfacts(symbol, timeout=timeout)
    if not companyfacts:
        return {}, {"error": "sec_companyfacts_unavailable", "sec_meta": meta}
    mapping = {
        "revenue": ["RevenueFromContractWithCustomerExcludingAssessedTax", "Revenues", "SalesRevenueNet"],
        "gross_profit": ["GrossProfit"],
        "operating_income": ["OperatingIncomeLoss"],
        "net_income": ["NetIncomeLoss", "ProfitLoss"],
        "eps_basic": ["EarningsPerShareBasic"],
        "eps_diluted": ["EarningsPerShareDiluted"],
        "operating_cash_flow": ["NetCashProvidedByUsedInOperatingActivities"],
        "capex": ["PaymentsToAcquirePropertyPlantAndEquipment"],
        "cash_and_equivalents": ["CashAndCashEquivalentsAtCarryingValue", "CashCashEquivalentsRestrictedCashAndRestrictedCashEquivalents"],
        "total_debt": ["LongTermDebtAndFinanceLeaseObligationsCurrentAndNoncurrent", "LongTermDebtCurrent", "LongTermDebtNoncurrent"],
        "shareholders_equity": ["StockholdersEquity"],
    }
    values: dict[str, Any] = {}
    source_rows: dict[str, Any] = {}
    for field, concepts in mapping.items():
        value, row = latest_fact(companyfacts, concepts)
        values[field] = value
        if row:
            source_rows[field] = row
    period_mismatches: list[str] = []
    if values.get("operating_cash_flow") is not None and values.get("capex") is not None and same_fact_period(source_rows.get("operating_cash_flow"), source_rows.get("capex")):
        values["free_cash_flow"] = values["operating_cash_flow"] - abs(values["capex"])
    elif values.get("operating_cash_flow") is not None and values.get("capex") is not None:
        period_mismatches.append("free_cash_flow: operating_cash_flow/capex periods differ")
    if values.get("gross_profit") is not None and values.get("revenue") and same_fact_period(source_rows.get("gross_profit"), source_rows.get("revenue")):
        values["gross_margin"] = values["gross_profit"] / values["revenue"]
    elif values.get("gross_profit") is not None and values.get("revenue"):
        period_mismatches.append("gross_margin: gross_profit/revenue periods differ")
    if values.get("operating_income") is not None and values.get("revenue") and same_fact_period(source_rows.get("operating_income"), source_rows.get("revenue")):
        values["operating_margin"] = values["operating_income"] / values["revenue"]
    elif values.get("operating_income") is not None and values.get("revenue"):
        period_mismatches.append("operating_margin: operating_income/revenue periods differ")
    if values.get("net_income") is not None and values.get("revenue") and same_fact_period(source_rows.get("net_income"), source_rows.get("revenue")):
        values["net_margin"] = values["net_income"] / values["revenue"]
    elif values.get("net_income") is not None and values.get("revenue"):
        period_mismatches.append("net_margin: net_income/revenue periods differ")
    if values.get("net_income") is not None and values.get("shareholders_equity") and same_fact_period(source_rows.get("net_income"), source_rows.get("shareholders_equity")):
        values["roe"] = values["net_income"] / values["shareholders_equity"]
    elif values.get("net_income") is not None and values.get("shareholders_equity"):
        period_mismatches.append("roe: net_income/shareholders_equity periods differ")
    latest_period = latest_source_period(source_rows)
    metadata = {
        "sec_meta": meta,
        "source": "sec_companyfacts",
        "source_url": sec_companyfacts_url(meta["cik"]) if meta else None,
        "source_rows": source_rows,
        "period_mismatches": period_mismatches,
    }
    values["period"] = latest_period.get("end")
    values["fiscal_year"] = latest_period.get("fy")
    values["fiscal_quarter"] = latest_period.get("fp")
    return values, metadata


def build_factor_fundamentals(conn: sqlite3.Connection, ticker: str) -> tuple[dict[str, Any], dict[str, Any]]:
    values = {
        "revenue": factor_value(conn, ticker, ["revenue"]),
        "net_income": factor_value(conn, ticker, ["net_profit", "holder_profit"]),
        "eps_basic": factor_value(conn, ticker, ["basic_eps_reported", "eps_ttm"]),
        "gross_margin": factor_value(conn, ticker, ["gross_margin"]),
        "operating_cash_flow": factor_value(conn, ticker, ["ocf_per_share"]),
        "cash_and_equivalents": None,
        "total_debt": None,
    }
    values["period"] = latest_factor_date(conn, ticker)
    return values, {"source": "factor_daily", "factor_trade_date": values["period"]}


def _normalize_extract_value(value: Any) -> float | None:
    if value in (None, "", "None", "-", "--", "nan"):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).replace(",", "").strip()
    try:
        return float(text)
    except ValueError:
        return None


def _field_detail_defaults(field: str, market: str | None, period: str | None, missing_reason: str) -> dict[str, Any]:
    return {
        "field": field,
        "extracted_value": None,
        "unit": default_currency_for_market(market),
        "currency": default_currency_for_market(market),
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


def _merge_field_details(
    market: str | None,
    base_period: str | None,
    extracted: dict[str, Any] | None,
    existing_values: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any], list[str], dict[str, str], list[str], float, str]:
    field_details: dict[str, Any] = {}
    field_values: dict[str, Any] = {}
    missing_fields: list[str] = []
    missing_reasons: dict[str, str] = {}
    evidence_ids: list[str] = []
    confidence_buckets: list[float] = []
    source_quality = "secondary"
    freshness_status = "missing"
    extracted = extracted or {}
    extracted_details = extracted.get("field_details") or {}
    extracted_values = extracted.get("field_values") or {}
    field_missing_reasons = extracted.get("field_missing_reasons") or {}

    for field in FUNDAMENTAL_FIELDS:
        detail = extracted_details.get(field)
        if detail is None:
            detail = _field_detail_defaults(field, market, base_period, field_missing_reasons.get(field, "field_not_found"))
        detail = dict(detail)
        if detail.get("extracted_value") is None and existing_values.get(field) is not None:
            detail["extracted_value"] = existing_values[field]
            detail["unit"] = detail.get("unit") or default_currency_for_market(market)
            detail["currency"] = detail.get("currency") or default_currency_for_market(market)
            detail["confidence"] = max(float(detail.get("confidence") or 0.0), 0.35)
            detail["missing_reason"] = None
            if detail.get("source_evidence_id"):
                evidence_ids.append(str(detail["source_evidence_id"]))
        if detail.get("extracted_value") is not None:
            field_values[field] = _normalize_extract_value(detail.get("extracted_value"))
            if field_values[field] is None:
                detail["missing_reason"] = "parse_failed"
                missing_fields.append(field)
                missing_reasons[field] = "parse_failed"
            else:
                confidence_buckets.append(float(detail.get("confidence") or 0.0))
                source_quality = "primary"
                if detail.get("source_evidence_id"):
                    evidence_ids.append(str(detail["source_evidence_id"]))
        else:
            missing_fields.append(field)
            missing_reasons[field] = detail.get("missing_reason") or field_missing_reasons.get(field) or "field_not_found"
        field_details[field] = detail

    evidence_ids = list(dict.fromkeys(item for item in evidence_ids if item))
    present_count = len([field for field in FUNDAMENTAL_FIELDS if field_values.get(field) is not None])
    if extracted and extracted.get("freshness_status") == "fresh":
        freshness_status = "fresh"
    elif present_count >= 4:
        freshness_status = "fresh"
    elif present_count >= 1:
        freshness_status = "degraded"
    elif extracted and extracted.get("freshness_status") == "degraded":
        freshness_status = "degraded"
    elif extracted and extracted.get("freshness_status") == "stale":
        freshness_status = "stale"
    else:
        freshness_status = "missing"
    confidence = round(min(0.95, max(confidence_buckets or [0.0]) if confidence_buckets else 0.0), 3) if confidence_buckets else 0.0
    if not confidence and extracted:
        confidence = float(extracted.get("confidence") or 0.0)
    if present_count:
        confidence = round(min(0.95, max(confidence, 0.25 + present_count / len(FUNDAMENTAL_FIELDS) * 0.5)), 3)
    return field_details, field_values, missing_fields, missing_reasons, evidence_ids, confidence, freshness_status


def _annotate_snapshot_with_relationships(snapshot: dict[str, Any]) -> None:
    revenue = snapshot.get("revenue")
    gross_profit = snapshot.get("gross_profit")
    operating_income = snapshot.get("operating_income")
    net_income = snapshot.get("net_income")
    equity = snapshot.get("shareholders_equity")
    if revenue not in (None, 0) and gross_profit not in (None, 0):
        snapshot["gross_margin"] = gross_profit / revenue
    if revenue not in (None, 0) and operating_income not in (None, 0):
        snapshot["operating_margin"] = operating_income / revenue
    if revenue not in (None, 0) and net_income not in (None, 0):
        snapshot["net_margin"] = net_income / revenue
    if equity not in (None, 0) and net_income not in (None, 0):
        snapshot["roe"] = net_income / equity
    if equity not in (None, 0) and operating_income not in (None, 0):
        snapshot["roic"] = operating_income / equity
    if snapshot.get("operating_cash_flow") not in (None, 0) and snapshot.get("capex") not in (None, 0):
        snapshot["free_cash_flow"] = snapshot["operating_cash_flow"] - abs(snapshot["capex"])


def infer_from_filing_text(conn: sqlite3.Connection, ticker: str) -> tuple[dict[str, Any], dict[str, Any]]:
    if not relation_exists(conn, "document_chunks"):
        return {}, {"source": "filing_chunks", "matched_chunks": 0}
    rows = conn.execute(
        """
        SELECT text, evidence_id
        FROM document_chunks
        WHERE ticker=?
        ORDER BY created_at DESC
        LIMIT 20
        """,
        (ticker,),
    ).fetchall()
    text = "\n".join(row[0] for row in rows)
    values: dict[str, Any] = {}
    patterns = {
        "revenue": r"(?:revenue|收入)[^\d]{0,40}([0-9][0-9,\.]+)",
        "net_income": r"(?:net income|净利润)[^\d]{0,40}([0-9][0-9,\.]+)",
        "eps_basic": r"(?:eps|每股收益)[^\d]{0,40}([0-9][0-9,\.]+)",
        "gross_margin": r"(?:gross margin|毛利率)[^\d]{0,40}([0-9][0-9,\.]+)%",
    }
    for field, pattern in patterns.items():
        match = re.search(pattern, text, flags=re.I)
        if match:
            value = normalize_numeric(match.group(1))
            if value is not None:
                values[field] = value / 100.0 if field.endswith("margin") and value > 1 else value
    return values, {"source": "filing_chunks", "matched_chunks": len(rows), "evidence_ids": [row[1] for row in rows if row[1]][:6]}


def infer_from_relevant_filing_text(conn: sqlite3.Connection, ticker: str) -> tuple[dict[str, Any], dict[str, Any]]:
    chunks = select_relevant_document_chunks(conn, ticker=ticker, limit=32, min_investment_relevance=0.45)
    if not chunks:
        return {}, {"source": "relevant_filing_chunks", "matched_chunks": 0, "selector_used": True}
    text = "\n".join(str(row.get("text") or "") for row in chunks)
    evidence_ids = [row.get("evidence_id") for row in chunks if row.get("evidence_id")]
    patterns = {
        "revenue": r"(?:revenue|net sales|total revenue|营业收入|收入|收益)[^\d]{0,50}([0-9][0-9,\.]+)",
        "net_income": r"(?:net income|profit attributable|归母净利润|净利润|本公司拥有人应占利润)[^\d]{0,50}([0-9][0-9,\.]+)",
        "eps_basic": r"(?:basic EPS|diluted EPS|EPS|每股收益|基本每股收益|摊薄每股收益)[^\d]{0,50}([0-9][0-9,\.]+)",
        "gross_margin": r"(?:gross margin|毛利率|gross profit margin)[^\d]{0,50}([0-9][0-9,\.]+)%",
        "operating_cash_flow": r"(?:net cash provided by operating activities|operating cash flow|经营活动产生的现金流量净额|经营活动现金流)[^\d]{0,60}([0-9][0-9,\.]+)",
        "free_cash_flow": r"(?:free cash flow|自由现金流)[^\d]{0,60}([0-9][0-9,\.]+)",
        "cash_and_equivalents": r"(?:cash and cash equivalents|cash|现金及现金等价物|现金及等价物)[^\d]{0,60}([0-9][0-9,\.]+)",
        "total_debt": r"(?:total debt|borrowings|债务|借款)[^\d]{0,60}([0-9][0-9,\.]+)",
    }
    values: dict[str, Any] = {}
    for field, pattern in patterns.items():
        match = re.search(pattern, text, flags=re.I)
        if match:
            value = normalize_numeric(match.group(1))
            if value is not None:
                values[field] = value / 100.0 if field.endswith("margin") and value > 1 else value
    return values, {
        "source": "relevant_filing_chunks",
        "matched_chunks": len(chunks),
        "selector_used": True,
        "section_types": sorted({str(row.get("chunk_section_type")) for row in chunks if row.get("chunk_section_type")}),
        "evidence_ids": evidence_ids[:8],
        "field_missing_reasons": {field: "field_not_found" for field in patterns if values.get(field) is None},
    }


def upsert_fundamentals_evidence(conn: sqlite3.Connection, ticker: str, snapshot: dict[str, Any]) -> str:
    ensure_claim_graph_tables(conn)
    text = (
        f"{ticker} fundamentals snapshot: revenue={snapshot.get('revenue')}, "
        f"net_income={snapshot.get('net_income')}, eps={snapshot.get('eps_basic') or snapshot.get('eps_diluted')}, "
        f"gross_margin={snapshot.get('gross_margin')}, fcf={snapshot.get('free_cash_flow')}."
    )
    evidence_id = f"ev_fundamentals_{ticker.replace('.', '_')}_{snapshot['snapshot_id'][-12:]}"
    upsert_evidence(
        conn,
        {
            "evidence_id": evidence_id,
            "source_key": "fundamentals_snapshot",
            "source_type": "fundamentals",
            "source_quality": "primary" if snapshot.get("source_quality") == "primary" else "secondary",
            "source_status": snapshot.get("freshness_status") or "active",
            "published_at": snapshot.get("period"),
            "ingested_at": snapshot.get("created_at"),
            "text_excerpt": text,
            "url_or_doc_id": snapshot["snapshot_id"],
            "metadata": {
                "ticker": ticker,
                "snapshot_id": snapshot["snapshot_id"],
                "missing_fields": snapshot.get("missing_fields") or [],
                "live": bool(snapshot.get("source_quality") == "primary"),
            },
        },
    )
    return evidence_id


def build_fundamentals_snapshot(
    conn: sqlite3.Connection,
    ticker: str,
    timeout: int = 30,
    prefer_live: bool = True,
) -> dict[str, Any]:
    ensure_fundamentals_tables(conn)
    market = market_for_ticker(ticker)
    errors: list[str] = []
    metadata: dict[str, Any] = {}
    values: dict[str, Any] = {}
    source_quality = "secondary"
    if market == "US" and prefer_live:
        try:
            values, metadata = build_us_fundamentals(ticker, timeout=timeout)
            if values:
                source_quality = "primary"
        except Exception as exc:
            errors.append(f"sec_companyfacts_failed: {exc}")
    if not values:
        values, metadata = build_factor_fundamentals(conn, ticker)
    filing_values, filing_metadata = infer_from_relevant_filing_text(conn, ticker)
    if not filing_values:
        filing_values, fallback_filing_metadata = infer_from_filing_text(conn, ticker)
        filing_metadata = {
            **fallback_filing_metadata,
            "relevant_selector": filing_metadata,
            "fallback_used": True,
        }
    filing_field_snapshot = extract_field_level_fundamentals(
        conn,
        ticker,
        market=market,
        limit=32,
        stale_after_days=365,
    )
    existing_values = {field: value for field, value in values.items() if value is not None}
    field_details, field_values, missing_fields, missing_reasons, source_evidence_ids, confidence, freshness_status = _merge_field_details(
        market,
        filing_metadata.get("period") or values.get("period") or filing_field_snapshot.get("latest_anchor"),
        filing_field_snapshot,
        existing_values,
    )
    for field, value in filing_values.items():
        if value is not None and field_values.get(field) is None:
            field_values[field] = value
            field_details[field]["extracted_value"] = value
            field_details[field]["confidence"] = max(float(field_details[field].get("confidence") or 0.0), 0.35)
            field_details[field]["missing_reason"] = None
    values = {**field_values, **{key: value for key, value in values.items() if value is not None}}
    _annotate_snapshot_with_relationships(values)
    metadata = {
        **metadata,
        "filing_inference": filing_metadata,
        "field_extraction": filing_field_snapshot,
        "errors": errors,
    }
    if filing_metadata.get("evidence_ids"):
        source_evidence_ids = list(dict.fromkeys(list(filing_metadata["evidence_ids"]) + source_evidence_ids))
    source_evidence_ids = list(dict.fromkeys(source_evidence_ids))
    present_count = len([field for field in FUNDAMENTAL_FIELDS if values.get(field) is not None])
    confidence = round(min(0.95, max(confidence, 0.25 + present_count / len(FUNDAMENTAL_FIELDS) * 0.5 + (0.05 if source_evidence_ids else 0.0))), 3)
    if freshness_status == "missing" and present_count >= 1:
        freshness_status = "degraded"
    effective_source_quality = "primary" if source_evidence_ids else source_quality
    snapshot_id = generate_execution_id("fundamentals")
    created_at = now_ts()
    snapshot = {
        "snapshot_id": snapshot_id,
        "ticker": ticker,
        "market": market,
        "period": values.get("period"),
        "fiscal_year": values.get("fiscal_year"),
        "fiscal_quarter": values.get("fiscal_quarter"),
        **{field: values.get(field) for field in FUNDAMENTAL_FIELDS},
        "source_evidence_ids": source_evidence_ids,
        "source_quality": effective_source_quality if present_count else "missing",
        "freshness_status": freshness_status,
        "confidence": confidence if present_count else 0.0,
        "missing_fields": missing_fields,
        "field_details": field_details,
        "field_missing_reasons": missing_reasons,
        "created_at": created_at,
        "metadata": metadata,
    }
    conn.execute(
        f"""
        INSERT INTO fundamentals_snapshot (
            snapshot_id, ticker, market, period, fiscal_year, fiscal_quarter,
            {', '.join(FUNDAMENTAL_FIELDS)},
            source_evidence_ids_json, source_quality, freshness_status, confidence,
            missing_fields_json, field_details_json, field_missing_reasons_json, created_at, metadata_json
        )
        VALUES (
            ?, ?, ?, ?, ?, ?,
            {', '.join('?' for _ in FUNDAMENTAL_FIELDS)},
            ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
        """,
        (
            snapshot_id,
            ticker,
            market,
            snapshot["period"],
            snapshot["fiscal_year"],
            snapshot["fiscal_quarter"],
            *[snapshot.get(field) for field in FUNDAMENTAL_FIELDS],
            json.dumps(source_evidence_ids, ensure_ascii=False),
            snapshot["source_quality"],
            snapshot["freshness_status"],
            snapshot["confidence"],
            json.dumps(missing_fields, ensure_ascii=False),
            json.dumps(field_details, ensure_ascii=False, sort_keys=True, default=str),
            json.dumps(missing_reasons, ensure_ascii=False, sort_keys=True, default=str),
            created_at,
            json.dumps(metadata, ensure_ascii=False, sort_keys=True, default=str),
        ),
    )
    evidence_id = upsert_fundamentals_evidence(conn, ticker, snapshot)
    snapshot["fundamentals_evidence_id"] = evidence_id
    return snapshot


def latest_fundamentals_snapshot(conn: sqlite3.Connection, ticker: str) -> dict[str, Any]:
    ensure_fundamentals_tables(conn)
    row = conn.execute(
        f"""
        SELECT snapshot_id, ticker, market, period, fiscal_year, fiscal_quarter,
               {', '.join(FUNDAMENTAL_FIELDS)},
               source_evidence_ids_json, source_quality, freshness_status, confidence,
               missing_fields_json, field_details_json, field_missing_reasons_json, created_at, metadata_json
        FROM fundamentals_snapshot
        WHERE ticker=?
        ORDER BY datetime(created_at) DESC, id DESC
        LIMIT 1
        """,
        (ticker,),
    ).fetchone()
    if not row:
        return {}
    keys = [
        "snapshot_id",
        "ticker",
        "market",
        "period",
        "fiscal_year",
        "fiscal_quarter",
        *FUNDAMENTAL_FIELDS,
        "source_evidence_ids_json",
        "source_quality",
        "freshness_status",
        "confidence",
        "missing_fields_json",
        "field_details_json",
        "field_missing_reasons_json",
        "created_at",
        "metadata_json",
    ]
    data = dict(zip(keys, row))
    data["source_evidence_ids"] = loads_json(data.pop("source_evidence_ids_json"), [])
    data["missing_fields"] = loads_json(data.pop("missing_fields_json"), [])
    data["field_details"] = loads_json(data.pop("field_details_json"), {})
    data["field_missing_reasons"] = loads_json(data.pop("field_missing_reasons_json"), {})
    data["metadata"] = loads_json(data.pop("metadata_json"), {})
    return data
