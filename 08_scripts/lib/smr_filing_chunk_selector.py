#!/usr/bin/env python3
"""Filing chunk relevance scoring and selection helpers.

The goal is not to make every chunk look useful. The goal is to separate
investment-bearing text from metadata, boilerplate, and taxonomy noise so the
rest of the live pipeline can focus on actual evidence.
"""

from __future__ import annotations

import json
import re
import sqlite3
from typing import Any


NOISE_SECTION_TYPES = {
    "cover_page",
    "exhibit_index",
    "signature",
    "legal_boilerplate",
    "administrative",
}

CORE_SECTION_TYPES = {
    "financial_statement",
    "management_discussion",
    "guidance_outlook",
    "business_update",
    "segment_performance",
    "liquidity_capital",
    "shareholder_return",
}

PROXY_SECTION_TYPES = {
    "financial_statement",
    "management_discussion",
    "guidance_outlook",
    "business_update",
    "segment_performance",
    "liquidity_capital",
    "shareholder_return",
    "risk_factor",
}

FIELD_KEYWORDS = {
    "financial_statement": (
        "revenue",
        "net sales",
        "income from operations",
        "operating income",
        "gross profit",
        "net income",
        "earnings per share",
        "eps",
        "营业收入",
        "收入",
        "净利润",
        "毛利",
        "每股收益",
        "经营收入",
    ),
    "guidance_outlook": (
        "guidance",
        "outlook",
        "forecast",
        "estimate",
        "expects",
        "expectation",
        "指引",
        "展望",
        "预计",
        "预期",
        "预测",
    ),
    "risk_factor": (
        "risk factor",
        "risk factors",
        "uncertainty",
        "headwind",
        "风险因素",
        "风险",
        "不确定",
        "压力",
    ),
    "business_update": (
        "business update",
        "strategic",
        "commercialization",
        "demand",
        "customer",
        "cloud",
        "ai",
        "merchant",
        "产品",
        "业务",
        "经营",
        "战略",
    ),
    "segment_performance": (
        "segment",
        "segments",
        "分部",
        "业务板块",
        "板块",
    ),
    "liquidity_capital": (
        "cash",
        "liquidity",
        "debt",
        "borrow",
        "capital",
        "operating cash flow",
        "free cash flow",
        "现金",
        "流动性",
        "负债",
        "资本",
        "现金流",
    ),
    "shareholder_return": (
        "buyback",
        "repurchase",
        "dividend",
        "shareholder return",
        "shareholder returns",
        "回购",
        "分红",
        "股东回报",
    ),
}

NOISE_MARKERS = (
    "snapshot meta",
    "source_url",
    "source_kind",
    "fetched_at",
    "raw_rel_path",
    "meta_rel_path",
    "notice_date",
    "announcement_id",
    "sec_code",
    "content_type",
    "entity_type",
    "entity_id",
    "source_domain",
    "source_id",
    "title:",
    "published_at:",
)

TAXONOMY_MARKERS = (
    "us-gaap:",
    "ifrs-full:",
    "member",
    "axis",
    "domain",
    "dimension",
    "table",
)

ADMINISTRATIVE_MARKERS = (
    "trading symbol",
    "nasdaq global select market",
    "emerging growth company",
    "pre-commencement communications",
    "rule 425",
    "rule 14a-12",
    "rule 14d-2",
    "rule 13e-4",
    "departure of directors",
    "election of directors",
    "appointment of certain officers",
    "compensatory arrangements",
    "variable compensation plan",
    "target award opportunity",
    "annual base salary",
    "restricted stock units",
    "indemnity agreement",
    "signature pursuant to the requirements",
)

PROXY_SIGNAL_MARKERS = (
    "beat",
    "beats",
    "better-than-expected",
    "exceeded estimates",
    "above expectations",
    "above prior outlook",
    "raised guidance",
    "raises guidance",
    "higher guidance",
    "forecast for growth",
    "revenue guidance",
    "gross margin guidance",
    "eps guidance",
    "price-target hikes",
    "price target",
)


def relation_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name=?",
        (name,),
    ).fetchone()
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


def normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def ensure_filing_chunk_relevance_columns(conn: sqlite3.Connection) -> None:
    if not relation_exists(conn, "document_chunks"):
        return
    columns = table_columns(conn, "document_chunks")
    additions = {
        "chunk_section_type": "TEXT",
        "investment_relevance_score": "REAL",
        "financial_table_score": "REAL",
        "guidance_relevance_score": "REAL",
        "risk_relevance_score": "REAL",
        "business_update_score": "REAL",
        "exclude_reason": "TEXT",
        "usable_for_core_claim": "INTEGER NOT NULL DEFAULT 0",
        "usable_for_proxy_signal": "INTEGER NOT NULL DEFAULT 0",
    }
    for column, ddl in additions.items():
        if column not in columns:
            conn.execute(f"ALTER TABLE document_chunks ADD COLUMN {column} {ddl}")


def _count_hits(text: str, keywords: tuple[str, ...]) -> int:
    lower = text.lower()
    return sum(1 for keyword in keywords if keyword in lower)


def _numeric_density(text: str) -> float:
    if not text:
        return 0.0
    digits = len(re.findall(r"\d", text))
    return min(1.0, digits / max(len(text), 1) * 45.0)


def _noise_score(text: str) -> float:
    lower = text.lower()
    marker_hits = sum(1 for marker in NOISE_MARKERS if marker in lower)
    taxonomy_hits = sum(1 for marker in TAXONOMY_MARKERS if marker in lower)
    return min(1.0, marker_hits * 0.12 + taxonomy_hits * 0.06)


def _administrative_score(text: str) -> float:
    lower = text.lower()
    hits = sum(1 for marker in ADMINISTRATIVE_MARKERS if marker in lower)
    return min(1.0, hits * 0.16)


def _proxy_signal_score(text: str) -> float:
    lower = text.lower()
    hits = sum(1 for marker in PROXY_SIGNAL_MARKERS if marker in lower)
    return min(1.0, hits * 0.22)


def classify_chunk_text(
    text: str,
    section_name: str | None = None,
    filing_type: str | None = None,
    title: str | None = None,
    source_key: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    clean = normalize_text(text)
    lower = clean.lower()
    section_hint = normalize_text(section_name).lower()
    title_text = normalize_text(title).lower()
    metadata = metadata or {}

    if not clean:
        return {
            "chunk_section_type": "unknown",
            "investment_relevance_score": 0.0,
            "financial_table_score": 0.0,
            "guidance_relevance_score": 0.0,
            "risk_relevance_score": 0.0,
            "business_update_score": 0.0,
            "exclude_reason": "empty_chunk",
            "usable_for_core_claim": False,
            "usable_for_proxy_signal": False,
        }

    noise_score = _noise_score(clean)
    administrative_score = _administrative_score(clean)
    proxy_signal_score = _proxy_signal_score(clean)
    numeric_density = _numeric_density(clean)
    financial_hits = _count_hits(clean, FIELD_KEYWORDS["financial_statement"])
    guidance_hits = _count_hits(clean, FIELD_KEYWORDS["guidance_outlook"])
    risk_hits = _count_hits(clean, FIELD_KEYWORDS["risk_factor"])
    business_hits = _count_hits(clean, FIELD_KEYWORDS["business_update"])
    segment_hits = _count_hits(clean, FIELD_KEYWORDS["segment_performance"])
    liquidity_hits = _count_hits(clean, FIELD_KEYWORDS["liquidity_capital"])
    shareholder_hits = _count_hits(clean, FIELD_KEYWORDS["shareholder_return"])

    has_investment_hits = any(
        count > 0
        for count in (
            financial_hits,
            guidance_hits,
            risk_hits,
            business_hits,
            segment_hits,
            liquidity_hits,
            shareholder_hits,
        )
    )

    if administrative_score >= 0.48 and guidance_hits == 0 and proxy_signal_score == 0:
        section_type = "administrative"
    elif any(marker in lower for marker in ("snapshot meta", "source_url", "fetched_at", "announcement_id")) and not has_investment_hits:
        section_type = "cover_page"
    elif noise_score >= 0.72 and not has_investment_hits:
        section_type = "administrative"
    elif "signature" in lower and not has_investment_hits:
        section_type = "signature"
    elif "exhibit" in lower and "index" in lower and not has_investment_hits:
        section_type = "exhibit_index"
    elif noise_score >= 0.38 and len(clean) < 240 and not has_investment_hits:
        section_type = "legal_boilerplate"
    elif guidance_hits >= 1:
        section_type = "guidance_outlook"
    elif financial_hits >= 2:
        section_type = "financial_statement"
    elif segment_hits >= 1:
        section_type = "segment_performance"
    elif liquidity_hits >= 1:
        section_type = "liquidity_capital"
    elif shareholder_hits >= 1:
        section_type = "shareholder_return"
    elif risk_hits >= 1:
        section_type = "risk_factor"
    elif business_hits >= 2 or any(token in lower for token in ("management discussion", "business update", "operating update", "经营情况", "业务更新")):
        section_type = "business_update"
    elif "results" in lower or "earnings" in lower or "业绩" in clean:
        section_type = "management_discussion"
    else:
        section_type = "unknown"

    base_scores = {
        "financial_statement": 0.92,
        "guidance_outlook": 0.88,
        "management_discussion": 0.74,
        "segment_performance": 0.72,
        "liquidity_capital": 0.7,
        "business_update": 0.66,
        "shareholder_return": 0.62,
        "risk_factor": 0.58,
        "unknown": 0.3,
        "cover_page": 0.02,
        "exhibit_index": 0.02,
        "signature": 0.0,
        "legal_boilerplate": 0.08,
        "administrative": 0.05,
    }
    investment_relevance = base_scores.get(section_type, 0.3)
    financial_table_score = min(1.0, 0.18 + financial_hits * 0.15 + numeric_density * 0.35)
    guidance_relevance_score = min(1.0, 0.12 + guidance_hits * 0.22 + numeric_density * 0.15 + proxy_signal_score * 0.22)
    risk_relevance_score = min(1.0, 0.12 + risk_hits * 0.22 + max(0.0, noise_score * 0.05))
    business_update_score = min(1.0, 0.14 + business_hits * 0.14 + segment_hits * 0.1 + shareholder_hits * 0.06)

    if any(token in lower for token in ("increase", "decrease", "growth", "guidance", "outlook", "revenue", "income", "profit", "cash", "margin")):
        investment_relevance += 0.05
    if numeric_density >= 0.08:
        investment_relevance += 0.05
    if proxy_signal_score >= 0.22:
        investment_relevance += 0.08
    if source_key in {"sec_filing_document", "sec_earnings_material", "hkex_announcement", "cninfo_announcement", "official_ir_material"}:
        investment_relevance += 0.04
    if title_text and title_text not in clean.lower():
        investment_relevance += 0.01
    investment_relevance -= noise_score * 0.42
    investment_relevance -= administrative_score * 0.55
    if section_type in NOISE_SECTION_TYPES:
        investment_relevance = min(investment_relevance, 0.1)

    if section_type in NOISE_SECTION_TYPES:
        exclude_reason = f"noise_section:{section_type}"
    elif administrative_score >= 0.48 and proxy_signal_score == 0:
        exclude_reason = "administrative_low_signal"
    elif investment_relevance < 0.18:
        exclude_reason = "low_investment_relevance"
    else:
        exclude_reason = None

    usable_for_proxy_signal = (
        section_type in PROXY_SECTION_TYPES
        and investment_relevance >= 0.55
        and exclude_reason is None
        and (proxy_signal_score >= 0.22 or guidance_hits > 0 or financial_hits >= 2 or section_type == "financial_statement")
    )
    usable_for_core_claim = (
        section_type in CORE_SECTION_TYPES
        and investment_relevance >= 0.62
        and exclude_reason is None
    )

    return {
        "chunk_section_type": section_type,
        "investment_relevance_score": round(max(0.0, min(investment_relevance, 1.0)), 3),
        "financial_table_score": round(financial_table_score, 3),
        "guidance_relevance_score": round(guidance_relevance_score, 3),
        "risk_relevance_score": round(risk_relevance_score, 3),
        "business_update_score": round(business_update_score, 3),
        "exclude_reason": exclude_reason,
        "usable_for_core_claim": bool(usable_for_core_claim),
        "usable_for_proxy_signal": bool(usable_for_proxy_signal),
        "noise_score": round(noise_score, 3),
        "administrative_score": round(administrative_score, 3),
        "proxy_signal_score": round(proxy_signal_score, 3),
        "numeric_density": round(numeric_density, 3),
    }


def update_document_chunk_relevance(
    conn: sqlite3.Connection,
    ticker: str | None = None,
    document_id: str | None = None,
    limit: int = 2000,
) -> dict[str, Any]:
    ensure_filing_chunk_relevance_columns(conn)
    if not relation_exists(conn, "document_chunks"):
        return {"updated": 0, "usable_for_core_claim": 0, "usable_for_proxy_signal": 0}
    params: list[Any] = []
    where = []
    if ticker:
        where.append("c.ticker=?")
        params.append(ticker)
    if document_id:
        where.append("c.document_id=?")
        params.append(document_id)
    where_sql = f"WHERE {' AND '.join(where)}" if where else ""
    rows = conn.execute(
        f"""
        SELECT
            c.chunk_id,
            c.document_id,
            c.section_name,
            c.text,
            c.metadata_json,
            c.source_key,
            c.ticker,
            c.market,
            f.title,
            f.filing_type
        FROM document_chunks c
        LEFT JOIN filing_documents f ON f.filing_id=c.document_id
        {where_sql}
        ORDER BY COALESCE(f.published_at, f.ingested_at, c.created_at) DESC, c.chunk_index ASC
        LIMIT ?
        """,
        (*params, limit),
    ).fetchall()
    updated = 0
    core_count = 0
    proxy_count = 0
    for row in rows:
        metadata = loads_json(row[4], {})
        profile = classify_chunk_text(
            row[3],
            section_name=row[2],
            filing_type=row[9],
            title=row[8],
            source_key=row[5],
            metadata=metadata,
        )
        conn.execute(
            """
            UPDATE document_chunks
            SET chunk_section_type=?,
                investment_relevance_score=?,
                financial_table_score=?,
                guidance_relevance_score=?,
                risk_relevance_score=?,
                business_update_score=?,
                exclude_reason=?,
                usable_for_core_claim=?,
                usable_for_proxy_signal=?
            WHERE chunk_id=?
            """,
            (
                profile["chunk_section_type"],
                profile["investment_relevance_score"],
                profile["financial_table_score"],
                profile["guidance_relevance_score"],
                profile["risk_relevance_score"],
                profile["business_update_score"],
                profile["exclude_reason"],
                1 if profile["usable_for_core_claim"] else 0,
                1 if profile["usable_for_proxy_signal"] else 0,
                row[0],
            ),
        )
        updated += 1
        core_count += 1 if profile["usable_for_core_claim"] else 0
        proxy_count += 1 if profile["usable_for_proxy_signal"] else 0
    return {"updated": updated, "usable_for_core_claim": core_count, "usable_for_proxy_signal": proxy_count}


def select_relevant_document_chunks(
    conn: sqlite3.Connection,
    ticker: str | None = None,
    document_id: str | None = None,
    limit: int = 24,
    min_investment_relevance: float = 0.55,
    proxy_only: bool = False,
) -> list[dict[str, Any]]:
    ensure_filing_chunk_relevance_columns(conn)
    if not relation_exists(conn, "document_chunks"):
        return []
    update_document_chunk_relevance(conn, ticker=ticker, document_id=document_id, limit=max(limit * 4, 64))
    params: list[Any] = [min_investment_relevance]
    where = ["COALESCE(c.investment_relevance_score, 0) >= ?"]
    if ticker:
        where.append("c.ticker=?")
        params.append(ticker)
    if document_id:
        where.append("c.document_id=?")
        params.append(document_id)
    if proxy_only:
        where.append("COALESCE(c.usable_for_proxy_signal, 0)=1")
    else:
        where.append("(COALESCE(c.usable_for_core_claim, 0)=1 OR COALESCE(c.usable_for_proxy_signal, 0)=1)")
    where_sql = " AND ".join(where)
    rows = conn.execute(
        f"""
        SELECT
            c.chunk_id,
            c.document_id,
            c.document_type,
            c.source_key,
            c.ticker,
            c.market,
            c.section_name,
            c.chunk_index,
            c.text,
            c.evidence_id,
            c.created_at,
            c.metadata_json,
            c.chunk_section_type,
            c.investment_relevance_score,
            c.financial_table_score,
            c.guidance_relevance_score,
            c.risk_relevance_score,
            c.business_update_score,
            c.exclude_reason,
            c.usable_for_core_claim,
            c.usable_for_proxy_signal,
            f.title,
            f.filing_type,
            f.published_at,
            f.ingested_at
        FROM document_chunks c
        LEFT JOIN filing_documents f ON f.filing_id=c.document_id
        WHERE {where_sql}
        ORDER BY COALESCE(f.published_at, f.ingested_at, c.created_at) DESC,
                 COALESCE(c.guidance_relevance_score, 0) DESC,
                 COALESCE(c.financial_table_score, 0) DESC,
                 COALESCE(c.investment_relevance_score, 0) DESC,
                 c.chunk_index ASC
        LIMIT ?
        """,
        (*params, limit),
    ).fetchall()
    results = []
    for row in rows:
        results.append(
            {
                "chunk_id": row[0],
                "document_id": row[1],
                "document_type": row[2],
                "source_key": row[3],
                "ticker": row[4],
                "market": row[5],
                "section_name": row[6],
                "chunk_index": row[7],
                "text": row[8],
                "evidence_id": row[9],
                "created_at": row[10],
                "metadata": loads_json(row[11], {}),
                "chunk_section_type": row[12],
                "investment_relevance_score": row[13],
                "financial_table_score": row[14],
                "guidance_relevance_score": row[15],
                "risk_relevance_score": row[16],
                "business_update_score": row[17],
                "exclude_reason": row[18],
                "usable_for_core_claim": bool(row[19]) if row[19] is not None else False,
                "usable_for_proxy_signal": bool(row[20]) if row[20] is not None else False,
                "title": row[21],
                "filing_type": row[22],
                "published_at": row[23],
                "ingested_at": row[24],
            }
        )
    return results
