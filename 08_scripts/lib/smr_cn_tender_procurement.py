#!/usr/bin/env python3
"""Phase 24 CN tender/procurement connector primitives.

Version 1 is deliberately conservative: it searches already-ingested local
evidence/news/filing rows and normalizes matches. It does not persist raw HTML,
download PDFs, or treat tender notices as confirmed awards.
"""

from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from datetime import datetime
from typing import Any

from smr_cn_tender_query_planner import build_cn_tender_queries, company_name_for_ticker, normalize_ticker


CONNECTOR_ID = "cn_tender_procurement"
CONNECTOR_STATUS = "partial"

TENDER_EVIDENCE_TYPES = {
    "tender_notice",
    "tender_award",
    "procurement_notice",
    "procurement_award",
    "winning_bid",
    "signed_contract",
    "framework_agreement",
    "customer_project",
    "customer_capex",
    "purchase_intention",
    "news_mention",
    "rumor_or_unconfirmed",
    "unknown",
}

TENDER_EVIDENCE_STRENGTHS = {
    "confirmed_award",
    "near_confirmed",
    "strong_indication",
    "medium_indication",
    "weak_indication",
    "context_only",
    "blocked",
}

AWARD_TERMS = ("中标", "成交", "结果公告", "中标结果", "中标公告", "winning bid", "awarded", "award result")
NOTICE_TERMS = ("招标公告", "采购公告", "询价公告", "招标", "采购需求", "tender notice", "procurement notice")
PROCUREMENT_TERMS = ("采购", "政府采购", "集采", "procurement", "purchase")
CONTRACT_TERMS = ("合同", "签订合同", "重大合同", "signed contract", "contract")
FRAMEWORK_TERMS = ("框架协议", "战略合作协议", "framework agreement")
CAPEX_TERMS = ("智算中心", "数据中心", "算力中心", "算力", "服务器", "AI服务器", "GPU服务器", "capex", "data center")
INTENTION_TERMS = ("采购意向", "意向公告", "拟采购", "purchase intention")
RUMOR_TERMS = ("传闻", "网传", "未经证实", "rumor", "unconfirmed")
NEWS_TERMS = ("新闻", "转载", "报道", "news")


def now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def dumps_json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, sort_keys=True, default=str)


def loads_json(raw: str | None, fallback: Any) -> Any:
    if raw in (None, ""):
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def table_exists(conn: sqlite3.Connection, name: str) -> bool:
    return bool(conn.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name=?", (name,)).fetchone())


def stable_tender_key(*parts: Any, prefix: str = "cn_tender") -> str:
    raw = "|".join(str(part or "") for part in parts)
    return f"{prefix}_{hashlib.sha1(raw.encode('utf-8')).hexdigest()[:18]}"


def contains_any(text: str, terms: tuple[str, ...]) -> bool:
    lower = str(text or "").lower()
    return any(term.lower() in lower for term in terms)


def extract_amount(text: str) -> float | None:
    match = re.search(r"([0-9]+(?:,[0-9]{3})*(?:\.[0-9]+)?)\s*(?:亿元|万元|元|million|billion)", str(text or ""), re.I)
    if not match:
        return None
    try:
        return float(match.group(1).replace(",", ""))
    except ValueError:
        return None


def classify_tender_evidence_type(text: str, *, source_type: str | None = None) -> str:
    haystack = str(text or "")
    source = str(source_type or "").lower()
    if contains_any(haystack, RUMOR_TERMS):
        return "rumor_or_unconfirmed"
    if source == "news" or contains_any(haystack, NEWS_TERMS):
        if contains_any(haystack, AWARD_TERMS + PROCUREMENT_TERMS + CONTRACT_TERMS):
            return "news_mention"
    if contains_any(haystack, CONTRACT_TERMS):
        return "signed_contract"
    if contains_any(haystack, FRAMEWORK_TERMS):
        return "framework_agreement"
    if contains_any(haystack, AWARD_TERMS) and contains_any(haystack, PROCUREMENT_TERMS):
        return "procurement_award"
    if contains_any(haystack, AWARD_TERMS):
        return "tender_award"
    if contains_any(haystack, INTENTION_TERMS):
        return "purchase_intention"
    if contains_any(haystack, NOTICE_TERMS) and contains_any(haystack, PROCUREMENT_TERMS):
        return "procurement_notice"
    if contains_any(haystack, NOTICE_TERMS):
        return "tender_notice"
    if contains_any(haystack, CAPEX_TERMS):
        return "customer_capex"
    return "unknown"


def tender_strength_for(
    evidence_type: str,
    *,
    source_url: str | None,
    is_company_named: bool,
    is_award_result: bool,
    is_news_reprint: bool,
    is_customer_named: bool,
) -> str:
    if evidence_type == "rumor_or_unconfirmed":
        return "blocked"
    if not source_url:
        return "blocked"
    if evidence_type == "news_mention" or is_news_reprint:
        return "context_only"
    if evidence_type in {"signed_contract", "winning_bid", "procurement_award", "tender_award"}:
        if is_company_named and is_award_result:
            return "confirmed_award" if is_customer_named else "near_confirmed"
        return "strong_indication"
    if evidence_type == "framework_agreement":
        return "near_confirmed" if is_company_named else "medium_indication"
    if evidence_type in {"tender_notice", "procurement_notice"}:
        return "medium_indication" if is_company_named else "weak_indication"
    if evidence_type in {"customer_project", "customer_capex", "purchase_intention"}:
        return "strong_indication" if is_customer_named else "medium_indication"
    return "context_only"


def allowed_usage_for_strength(evidence_type: str, strength: str) -> str:
    if strength == "blocked":
        return "blocked"
    if evidence_type == "news_mention" or strength == "context_only":
        return "context_only"
    if strength in {"confirmed_award", "near_confirmed", "strong_indication", "medium_indication"}:
        return "supporting_evidence"
    return "context_only"


def normalize_cn_tender_result(raw: dict[str, Any], *, ticker: str, company_name: str | None = None) -> dict[str, Any]:
    ticker = normalize_ticker(ticker)
    company = company_name_for_ticker(ticker, company_name)
    title = str(raw.get("title") or "").strip()
    snippet = str(raw.get("snippet") or raw.get("body") or raw.get("text") or "").strip()
    source_type = str(raw.get("source_type") or "").lower()
    source_url = str(raw.get("source_url") or raw.get("url") or "").strip() or None
    text = f"{title} {snippet}"
    evidence_type = str(raw.get("evidence_type") or "") or classify_tender_evidence_type(text, source_type=source_type)
    if evidence_type not in TENDER_EVIDENCE_TYPES:
        evidence_type = "unknown"
    is_company_named = bool(company and company in text) or ticker in text.upper()
    is_customer_named = bool(raw.get("customer_name")) or contains_any(text, ("客户", "采购人", "招标人", "业主", "运营商", "云厂商", "customer"))
    is_award_result = evidence_type in {"tender_award", "procurement_award", "winning_bid", "signed_contract"} or contains_any(text, AWARD_TERMS)
    is_tender_notice_only = evidence_type in {"tender_notice", "procurement_notice", "purchase_intention"}
    is_news_reprint = source_type == "news" or contains_any(text, NEWS_TERMS)
    strength = tender_strength_for(
        evidence_type,
        source_url=source_url,
        is_company_named=is_company_named,
        is_award_result=is_award_result,
        is_news_reprint=is_news_reprint,
        is_customer_named=is_customer_named,
    )
    limitations: list[str] = list(raw.get("limitations") or [])
    if evidence_type in {"tender_notice", "procurement_notice"}:
        limitations.append("notice only, not award result")
    if evidence_type == "purchase_intention":
        limitations.append("purchase intention, not confirmed order")
    if evidence_type == "customer_capex":
        limitations.append("customer-side capex, not company-specific order")
    if is_news_reprint:
        limitations.append("news/reprint source, not official award confirmation")
    if not source_url:
        limitations.append("missing source_url; cannot enter evidence graph")
    if not is_company_named:
        limitations.append("company not directly named")
    independent_source_key = str(raw.get("independent_source_key") or "") or stable_tender_key(ticker, source_url, title)
    return {
        "ticker": ticker,
        "company_name": company,
        "evidence_type": evidence_type,
        "evidence_strength": strength,
        "title": title or snippet[:120],
        "published_at": raw.get("published_at"),
        "source_name": raw.get("source_name") or "CN tender/procurement source",
        "source_url": source_url,
        "project_name": raw.get("project_name") or title or None,
        "customer_name": raw.get("customer_name"),
        "amount": raw.get("amount") if raw.get("amount") is not None else extract_amount(text),
        "currency": raw.get("currency") or "CNY",
        "is_company_named": is_company_named,
        "is_customer_named": is_customer_named,
        "is_award_result": is_award_result,
        "is_tender_notice_only": is_tender_notice_only,
        "is_news_reprint": is_news_reprint,
        "independent_source_key": independent_source_key,
        "limitations": list(dict.fromkeys(limitations)),
        "allowed_usage": allowed_usage_for_strength(evidence_type, strength),
        "source_type": source_type or "local_evidence_search",
        "snippet": snippet[:800],
        "metadata": {**(raw.get("metadata") or {}), "connector_id": CONNECTOR_ID, "raw_source_id": raw.get("raw_source_id")},
    }


def _source_url_from(value: Any) -> str | None:
    text = str(value or "").strip()
    return text if text.startswith(("http://", "https://")) else None


def _metadata_source_url(metadata: dict[str, Any]) -> str | None:
    return _source_url_from(metadata.get("source_url") or metadata.get("url") or metadata.get("source"))


def _row_matches(text: str, company: str | None) -> bool:
    return contains_any(text, AWARD_TERMS + NOTICE_TERMS + PROCUREMENT_TERMS + CONTRACT_TERMS + FRAMEWORK_TERMS + CAPEX_TERMS + INTENTION_TERMS)


def search_local_tender_sources(conn: sqlite3.Connection, ticker: str, *, company_name: str | None = None, limit: int = 50) -> list[dict[str, Any]]:
    ticker = normalize_ticker(ticker)
    company = company_name_for_ticker(ticker, company_name)
    if not ticker.endswith((".SZ", ".SH")) and not company:
        return []
    rows: list[dict[str, Any]] = []

    if table_exists(conn, "news_items"):
        for row in conn.execute(
            """
            SELECT news_id, source_key, source_name, title, body, url, published_at, metadata_json, tickers_json
            FROM news_items
            WHERE upper(COALESCE(tickers_json, '') || COALESCE(title, '') || COALESCE(body, '')) LIKE ?
               OR COALESCE(title, '') || COALESCE(body, '') LIKE ?
            ORDER BY datetime(COALESCE(published_at, ingested_at, '1970-01-01')) DESC
            LIMIT ?
            """,
            (f"%{ticker}%", f"%{company or ticker}%", max(limit, 20)),
        ).fetchall():
            text = f"{row[3] or ''} {row[4] or ''}"
            if not _row_matches(text, company):
                continue
            rows.append(
                {
                    "raw_source_id": row[0],
                    "source_type": "news",
                    "source_name": row[2] or row[1] or "news",
                    "title": row[3],
                    "snippet": row[4],
                    "source_url": _source_url_from(row[5]),
                    "published_at": row[6],
                    "metadata": loads_json(row[7], {}),
                }
            )

    if table_exists(conn, "filing_documents"):
        for row in conn.execute(
            """
            SELECT filing_id, source_key, company_name, title, source_url, published_at, filing_type, metadata_json
            FROM filing_documents
            WHERE upper(COALESCE(ticker, ''))=?
               OR COALESCE(company_name, '') || COALESCE(title, '') LIKE ?
            ORDER BY datetime(COALESCE(published_at, ingested_at, '1970-01-01')) DESC
            LIMIT ?
            """,
            (ticker, f"%{company or ticker}%", max(limit, 20)),
        ).fetchall():
            text = f"{row[2] or ''} {row[3] or ''}"
            if not _row_matches(text, company):
                continue
            rows.append(
                {
                    "raw_source_id": row[0],
                    "source_type": "filing",
                    "source_name": row[1] or "filing",
                    "title": row[3],
                    "snippet": text,
                    "source_url": _source_url_from(row[4]),
                    "published_at": row[5],
                    "metadata": {**loads_json(row[7], {}), "filing_type": row[6]},
                }
            )

    for table, text_col, id_col, url_col in (
        ("evidence_items", "text_excerpt", "evidence_id", "url_or_doc_id"),
        ("document_chunks", "text", "chunk_id", None),
    ):
        if not table_exists(conn, table):
            continue
        if table == "evidence_items":
            sql = """
                SELECT evidence_id, source_key, source_type, source_quality, published_at, text_excerpt, url_or_doc_id, metadata_json
                FROM evidence_items
                WHERE upper(COALESCE(metadata_json, '') || COALESCE(text_excerpt, '')) LIKE ?
                   OR COALESCE(text_excerpt, '') LIKE ?
                ORDER BY datetime(COALESCE(published_at, ingested_at, created_at, '1970-01-01')) DESC
                LIMIT ?
            """
            values = (f"%{ticker}%", f"%{company or ticker}%", max(limit, 30))
        else:
            sql = """
                SELECT chunk_id, source_key, document_type, 'secondary', created_at, text, NULL, metadata_json
                FROM document_chunks
                WHERE upper(COALESCE(ticker, ''))=?
                   OR COALESCE(metadata_json, '') || COALESCE(text, '') LIKE ?
                ORDER BY datetime(COALESCE(created_at, '1970-01-01')) DESC
                LIMIT ?
            """
            values = (ticker, f"%{company or ticker}%", max(limit, 30))
        for row in conn.execute(sql, values).fetchall():
            text = str(row[5] or "")
            if not _row_matches(text, company):
                continue
            rows.append(
                {
                    "raw_source_id": row[0],
                    "source_type": row[2] or table,
                    "source_name": row[1] or table,
                    "title": text[:140],
                    "snippet": text[:1200],
                    "source_url": _source_url_from(row[6]) or _metadata_source_url(loads_json(row[7], {})),
                    "published_at": row[4],
                    "metadata": loads_json(row[7], {}),
                    "source_quality": row[3],
                }
            )

    deduped: list[dict[str, Any]] = []
    seen: set[str] = set()
    for row in rows:
        key = str(row.get("source_url") or row.get("raw_source_id") or row.get("title"))
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)
    return deduped[:limit]


def build_cn_tender_procurement_payload(
    conn: sqlite3.Connection,
    ticker: str,
    *,
    company_name: str | None = None,
    thesis_type: str | None = "ai_infrastructure_demand",
    execute: bool = False,
    limit: int = 50,
) -> dict[str, Any]:
    from smr_tender_evidence_linkage import tender_item_to_evidence_candidate, upsert_tender_evidence_candidate

    ticker = normalize_ticker(ticker)
    company = company_name_for_ticker(ticker, company_name)
    queries = build_cn_tender_queries(ticker, company_name=company, thesis_type=thesis_type)
    raw_results = search_local_tender_sources(conn, ticker, company_name=company, limit=limit)
    normalized = [normalize_cn_tender_result(row, ticker=ticker, company_name=company) for row in raw_results]
    candidates = [tender_item_to_evidence_candidate(item) for item in normalized if item.get("source_url") and item.get("allowed_usage") != "blocked"]
    written = 0
    if execute:
        for candidate in candidates:
            if upsert_tender_evidence_candidate(conn, candidate):
                written += 1
    no_result_reason = None
    if not raw_results:
        no_result_reason = "no local tender/procurement rows found in existing evidence/news/filing tables"
    elif not candidates:
        no_result_reason = "local rows found but none had source_url and sufficient evidence quality for evidence graph candidate"
    return {
        "ticker": ticker,
        "company_name": company,
        "connector_id": CONNECTOR_ID,
        "mode": "execute" if execute else "dry_run",
        "queries_generated": len([query for query in queries if query.get("query")]),
        "queries": queries,
        "raw_results_found": len(raw_results),
        "normalized_items": len(normalized),
        "evidence_candidates": candidates,
        "normalized_results": normalized[:20],
        "evidence_candidates_written": written,
        "no_result_reason": no_result_reason,
        "connector_status": CONNECTOR_STATUS,
        "safety": {
            "dry_run_writes_evidence_graph": False if not execute else None,
            "raw_files_persisted": False,
            "paper_order_created": False,
            "promotion_rules_relaxed": False,
            "planned_connector_treated_as_implemented": False,
        },
    }
