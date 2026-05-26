#!/usr/bin/env python3
"""Evidence quality scoring for claim and promotion gates."""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime
from typing import Any

from smr_claim_graph import ensure_claim_graph_tables


QUALITY_BASE = {
    "primary": 0.58,
    "secondary": 0.42,
    "tertiary": 0.26,
    "weak": 0.12,
}


def parse_dt(value: Any) -> datetime | None:
    text = str(value or "").strip()
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


def loads_json(raw: str | None, fallback: Any) -> Any:
    if raw in (None, ""):
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def table_columns(conn: sqlite3.Connection, name: str) -> set[str]:
    row = conn.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name=?", (name,)).fetchone()
    if not row:
        return set()
    return {item[1] for item in conn.execute(f"PRAGMA table_info({name})").fetchall()}


def ensure_evidence_quality_columns(conn: sqlite3.Connection) -> None:
    ensure_claim_graph_tables(conn)
    columns = table_columns(conn, "evidence_items")
    additions = {
        "quality_score": "REAL",
        "directness": "TEXT",
        "independence": "TEXT",
        "recency_score": "REAL",
        "ticker_relevance": "REAL",
        "theme_relevance": "REAL",
        "quote_specificity": "REAL",
        "investment_relevance_score": "REAL",
        "section_type_score": "REAL",
        "usable_for_proxy_signal": "INTEGER",
        "usable_for_core_claim": "INTEGER",
        "usable_for_promotion": "INTEGER",
        "quality_metadata_json": "TEXT NOT NULL DEFAULT '{}'",
    }
    for column, ddl in additions.items():
        if column not in columns:
            conn.execute(f"ALTER TABLE evidence_items ADD COLUMN {column} {ddl}")


def source_status_multiplier(status: str | None) -> float:
    value = str(status or "active").lower()
    if value in {"active", "fresh"}:
        return 1.0
    if value in {"degraded", "warn"}:
        return 0.7
    if value in {"stale"}:
        return 0.35
    if value in {"planned", "disabled", "deprecated", "error"}:
        return 0.0
    return 0.55


def recency_score(published_at: Any, ingested_at: Any = None, now: datetime | None = None) -> float:
    now = now or datetime.now()
    anchor = parse_dt(published_at) or parse_dt(ingested_at)
    if not anchor:
        return 0.35
    age_days = max(0.0, (now - anchor).total_seconds() / 86400.0)
    if age_days <= 7:
        return 1.0
    if age_days <= 30:
        return 0.82
    if age_days <= 180:
        return 0.58
    if age_days <= 365:
        return 0.36
    return 0.18


def ticker_relevance_score(text: str, metadata: dict[str, Any], ticker: str | None = None) -> float:
    if not ticker:
        return 0.5
    raw_ticker = str(ticker).upper()
    aliases = {raw_ticker, raw_ticker.replace(".HK", ""), raw_ticker.replace(".SZ", ""), raw_ticker.replace(".SH", "")}
    metadata_text = json.dumps(metadata, ensure_ascii=False).upper()
    full_text = f"{text.upper()} {metadata_text}"
    return 1.0 if any(alias and alias in full_text for alias in aliases) else 0.35


def theme_relevance_score(text: str, metadata: dict[str, Any], theme: str | None = None) -> float:
    if not theme:
        return 0.5
    tokens = [token.lower() for token in re.split(r"[^A-Za-z0-9\u4e00-\u9fff]+", str(theme)) if len(token) >= 2]
    haystack = f"{text} {json.dumps(metadata, ensure_ascii=False)}".lower()
    if not tokens:
        return 0.5
    hits = sum(1 for token in tokens if token in haystack)
    return min(1.0, 0.35 + hits / max(len(tokens), 1) * 0.65)


def quote_specificity_score(text: str) -> float:
    clean = re.sub(r"\s+", " ", str(text or "")).strip()
    score = 0.25
    if len(clean) >= 160:
        score += 0.2
    if re.search(r"\d", clean):
        score += 0.2
    if any(
        token in clean.lower()
        for token in (
            "revenue",
            "eps",
            "cash",
            "margin",
            "guidance",
            "risk",
            "profit",
            "demand",
            "order",
            "contract",
            "customer",
            "ai server",
            "data center",
        )
    ):
        score += 0.2
    if any(token in clean for token in ("需求", "订单", "合同", "客户", "中标", "采购", "算力", "数据中心", "智算中心", "AI服务器")):
        score += 0.15
    if any(token in clean for token in ("收入", "利润", "现金流", "毛利率", "风险", "指引")):
        score += 0.15
    return min(score, 1.0)


def directness_for(score: float) -> str:
    if score >= 0.75:
        return "high"
    if score >= 0.5:
        return "medium"
    return "low"


def _float_or_none(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def section_type_score(section_type: str | None) -> float:
    value = str(section_type or "unknown").lower()
    return {
        "financial_statement": 1.0,
        "guidance_outlook": 0.96,
        "management_discussion": 0.82,
        "segment_performance": 0.78,
        "liquidity_capital": 0.76,
        "business_update": 0.72,
        "shareholder_return": 0.68,
        "risk_factor": 0.64,
        "unknown": 0.38,
        "legal_boilerplate": 0.1,
        "cover_page": 0.04,
        "exhibit_index": 0.04,
        "administrative": 0.03,
        "signature": 0.0,
    }.get(value, 0.35)


def score_evidence_row(row: sqlite3.Row | dict[str, Any], ticker: str | None = None, theme: str | None = None) -> dict[str, Any]:
    if isinstance(row, dict):
        data = row
    elif hasattr(row, "keys"):
        data = dict(row)
    else:
        keys = [
            "evidence_id",
            "source_key",
            "source_type",
            "source_quality",
            "source_status",
            "published_at",
            "ingested_at",
            "text_excerpt",
            "metadata_json",
        ]
        data = dict(zip(keys, row))
    metadata = loads_json(data.get("metadata_json"), {}) if isinstance(data.get("metadata_json"), str) else data.get("metadata_json") or {}
    text = str(data.get("text_excerpt") or "")
    source_quality = str(data.get("source_quality") or "weak").lower()
    source_type = str(data.get("source_type") or "").lower()
    base = QUALITY_BASE.get(source_quality, 0.12)
    status_mult = source_status_multiplier(data.get("source_status"))
    recency = recency_score(data.get("published_at"), data.get("ingested_at"))
    ticker_score = ticker_relevance_score(text, metadata, ticker or metadata.get("ticker"))
    theme_score = theme_relevance_score(text, metadata, theme)
    specificity = quote_specificity_score(text)
    has_selector_metadata = any(
        key in metadata
        for key in (
            "chunk_section_type",
            "investment_relevance_score",
            "usable_for_core_claim",
            "usable_for_proxy_signal",
            "exclude_reason",
        )
    )
    investment_relevance = _float_or_none(metadata.get("investment_relevance_score"))
    if investment_relevance is None:
        if source_type == "filing" and not has_selector_metadata:
            investment_relevance = max(0.55, specificity * 0.82)
        else:
            investment_relevance = 0.5 if source_type != "filing" else 0.38
    section_score = section_type_score(metadata.get("chunk_section_type"))
    directness_value = (ticker_score * 0.45) + (specificity * 0.4) + (theme_score * 0.15)
    score = (
        base * 0.34
        + recency * 0.16
        + ticker_score * 0.14
        + specificity * 0.12
        + theme_score * 0.05
        + investment_relevance * 0.13
        + section_score * 0.06
    ) * status_mult
    if source_type in {"filing", "fundamentals"}:
        score += 0.04
    if source_type == "filing" and investment_relevance < 0.35:
        score = min(score, 0.45)
    if metadata.get("exclude_reason"):
        score = min(score, 0.32)
    quality_score = round(max(0.0, min(score, 1.0)), 3)
    metadata_core_flag = metadata.get("usable_for_core_claim")
    metadata_proxy_flag = metadata.get("usable_for_proxy_signal")
    if source_type == "filing":
        usable_for_core = (
            quality_score >= 0.62
            and source_quality in {"primary", "secondary"}
            and status_mult > 0.5
            and (not has_selector_metadata or metadata_core_flag is not False)
            and investment_relevance >= 0.55
        )
        usable_for_promotion = (
            quality_score >= 0.68
            and status_mult > 0.5
            and (not has_selector_metadata or metadata_core_flag is True or metadata_proxy_flag is True)
            and (not has_selector_metadata or investment_relevance >= 0.6)
        )
    else:
        usable_for_core = quality_score >= 0.62 and source_quality in {"primary", "secondary"} and status_mult > 0.5
        usable_for_promotion = quality_score >= 0.68 and status_mult > 0.5
    return {
        "evidence_id": data.get("evidence_id"),
        "quality_score": quality_score,
        "directness": directness_for(directness_value),
        "independence": "independent",
        "recency_score": round(recency, 3),
        "ticker_relevance": round(ticker_score, 3),
        "theme_relevance": round(theme_score, 3),
        "quote_specificity": round(specificity, 3),
        "investment_relevance_score": round(investment_relevance, 3),
        "section_type_score": round(section_score, 3),
        "usable_for_proxy_signal": bool(metadata_proxy_flag) if source_type == "filing" else usable_for_promotion,
        "usable_for_core_claim": usable_for_core,
        "usable_for_promotion": usable_for_promotion,
        "metadata": {
            "source_quality": source_quality,
            "source_type": source_type,
            "source_status_multiplier": status_mult,
            "chunk_section_type": metadata.get("chunk_section_type"),
            "investment_relevance_score": round(investment_relevance, 3),
            "section_type_score": round(section_score, 3),
            "usable_for_proxy_signal": bool(metadata_proxy_flag) if source_type == "filing" else usable_for_promotion,
        },
    }


def update_evidence_quality_scores(
    conn: sqlite3.Connection,
    ticker: str | None = None,
    theme: str | None = None,
    limit: int = 500,
) -> dict[str, Any]:
    ensure_evidence_quality_columns(conn)
    rows = conn.execute(
        """
        SELECT evidence_id, source_key, source_type, source_quality, source_status,
               published_at, ingested_at, text_excerpt, metadata_json
        FROM evidence_items
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    updated = 0
    usable_core = 0
    usable_promotion = 0
    for row in rows:
        scored = score_evidence_row(row, ticker=ticker, theme=theme)
        conn.execute(
            """
            UPDATE evidence_items
            SET quality_score=?, directness=?, independence=?, recency_score=?,
                ticker_relevance=?, theme_relevance=?, quote_specificity=?,
                investment_relevance_score=?, section_type_score=?, usable_for_proxy_signal=?,
                usable_for_core_claim=?, usable_for_promotion=?, quality_metadata_json=?
            WHERE evidence_id=?
            """,
            (
                scored["quality_score"],
                scored["directness"],
                scored["independence"],
                scored["recency_score"],
                scored["ticker_relevance"],
                scored["theme_relevance"],
                scored["quote_specificity"],
                scored["investment_relevance_score"],
                scored["section_type_score"],
                1 if scored["usable_for_proxy_signal"] else 0,
                1 if scored["usable_for_core_claim"] else 0,
                1 if scored["usable_for_promotion"] else 0,
                json.dumps(scored["metadata"], ensure_ascii=False, sort_keys=True),
                scored["evidence_id"],
            ),
        )
        updated += 1
        usable_core += 1 if scored["usable_for_core_claim"] else 0
        usable_promotion += 1 if scored["usable_for_promotion"] else 0
    return {
        "updated": updated,
        "usable_for_core_claim": usable_core,
        "usable_for_promotion": usable_promotion,
    }


def evidence_quality_summary(conn: sqlite3.Connection, evidence_ids: list[str] | None = None) -> dict[str, Any]:
    ensure_evidence_quality_columns(conn)
    params: list[Any] = []
    where = ""
    if evidence_ids:
        placeholders = ",".join("?" for _ in evidence_ids)
        where = f"WHERE evidence_id IN ({placeholders})"
        params.extend(evidence_ids)
    rows = conn.execute(
        f"""
        SELECT evidence_id, quality_score, usable_for_core_claim, usable_for_promotion, source_quality, source_type
        FROM evidence_items
        {where}
        """,
        tuple(params),
    ).fetchall()
    scores = [row[1] for row in rows if row[1] is not None]
    return {
        "evidence_count": len(rows),
        "min_quality_score": min(scores) if scores else None,
        "avg_quality_score": round(sum(scores) / len(scores), 3) if scores else None,
        "usable_for_core_claim_count": sum(1 for row in rows if row[2]),
        "usable_for_promotion_count": sum(1 for row in rows if row[3]),
        "primary_count": sum(1 for row in rows if row[4] == "primary"),
        "source_types": sorted({row[5] for row in rows if row[5]}),
    }


def evidence_quality_level(score: float | None, *, evidence_id: str | None = None, usable_for_promotion: bool = False) -> str:
    if not evidence_id:
        return "blocked"
    value = float(score or 0.0)
    if usable_for_promotion and value >= 0.68:
        return "high"
    if value >= 0.68:
        return "high"
    if value >= 0.55:
        return "medium"
    if value >= 0.35:
        return "low"
    return "blocked"


def score_tender_evidence_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    """Score a normalized tender/procurement candidate conservatively."""

    if not candidate.get("source_url"):
        return {
            "quality_score": 0.0,
            "quality_level": "blocked",
            "usable_for_bear_case_mitigation": False,
            "usable_for_proxy_signal": False,
            "remaining_issue": "missing_source_url",
        }
    strength = str(candidate.get("evidence_strength") or "")
    source_subtype = str(candidate.get("source_subtype") or candidate.get("evidence_type") or "")
    score = 0.42
    if strength == "confirmed_award":
        score += 0.28
    elif strength == "near_confirmed":
        score += 0.2
    elif strength == "strong_indication":
        score += 0.12
    elif strength == "medium_indication":
        score += 0.06
    if candidate.get("published_at"):
        score += 0.04
    if (candidate.get("metadata") or {}).get("is_company_named") or candidate.get("is_company_named"):
        score += 0.08
    if source_subtype in {"tender_notice", "procurement_notice", "purchase_intention", "news_mention"}:
        score = min(score, 0.58)
    if strength in {"blocked", "context_only"}:
        score = min(score, 0.34)
    quality_score = round(max(0.0, min(score, 1.0)), 3)
    quality_level = evidence_quality_level(quality_score, evidence_id=candidate.get("evidence_id"))
    return {
        "quality_score": quality_score,
        "quality_level": quality_level,
        "usable_for_bear_case_mitigation": quality_level in {"high", "medium"} and source_subtype not in {"tender_notice", "procurement_notice", "news_mention"},
        "usable_for_proxy_signal": quality_level in {"high", "medium", "low"} and strength != "blocked",
        "remaining_issue": None if quality_level in {"high", "medium"} else "quality_below_gate",
    }


def phase19_quality_dimensions(row: sqlite3.Row | dict[str, Any], ticker: str | None = None, theme: str | None = None) -> dict[str, Any]:
    if isinstance(row, dict):
        data = dict(row)
    elif hasattr(row, "keys"):
        data = dict(row)
    else:
        keys = [
            "evidence_id",
            "source_key",
            "source_type",
            "source_quality",
            "source_status",
            "published_at",
            "ingested_at",
            "text_excerpt",
            "metadata_json",
            "quality_score",
            "usable_for_core_claim",
            "usable_for_promotion",
        ]
        data = dict(zip(keys, row or []))
    scored = score_evidence_row(data, ticker=ticker, theme=theme)
    metadata = scored.get("metadata") or {}
    source_quality = str(data.get("source_quality") or metadata.get("source_quality") or "weak").lower()
    source_primary_score = {"primary": 1.0, "secondary": 0.75, "tertiary": 0.45, "weak": 0.2}.get(source_quality, 0.2)
    field_linkage_score = 1.0 if data.get("evidence_id") else 0.0
    if metadata.get("chunk_section_type") in {"financial_statement", "income_statement", "balance_sheet", "cash_flow_statement"}:
        field_linkage_score = max(field_linkage_score, 0.85)
    claim_relevance = round((scored.get("theme_relevance", 0.0) * 0.4) + (scored.get("investment_relevance_score", 0.0) * 0.6), 3)
    quality_level = evidence_quality_level(
        scored.get("quality_score"),
        evidence_id=scored.get("evidence_id"),
        usable_for_promotion=bool(scored.get("usable_for_promotion")),
    )
    usable_for_core = bool(scored.get("usable_for_core_claim")) and quality_level in {"high", "medium"}
    usable_for_promotion = bool(scored.get("usable_for_promotion")) and quality_level == "high"
    return {
        "evidence_id": scored.get("evidence_id"),
        "source_primary_score": round(source_primary_score, 3),
        "section_relevance_score": scored.get("section_type_score"),
        "freshness_score": scored.get("recency_score"),
        "ticker_relevance_score": scored.get("ticker_relevance"),
        "field_linkage_score": round(field_linkage_score, 3),
        "claim_relevance_score": claim_relevance,
        "overall_quality_score": scored.get("quality_score"),
        "quality_level": quality_level,
        "usable_for_core_claim": usable_for_core,
        "usable_for_promotion": usable_for_promotion,
        "remaining_issue": None if quality_level in {"high", "medium"} else ("missing_source_evidence_id" if not scored.get("evidence_id") else "quality_below_gate"),
    }


def _ticker_evidence_rows(conn: sqlite3.Connection, ticker: str, *, limit: int = 80) -> list[sqlite3.Row]:
    if not table_columns(conn, "evidence_items"):
        return []
    aliases = [str(ticker or "").upper()]
    if "." in aliases[0]:
        aliases.append(aliases[0].split(".", 1)[0])
    clauses = []
    params: list[Any] = []
    for alias in aliases:
        clauses.append("(metadata_json LIKE ? OR text_excerpt LIKE ? OR source_key LIKE ?)")
        params.extend([f"%{alias}%", f"%{alias}%", f"%{alias}%"])
    where = " OR ".join(clauses or ["1=0"])
    return conn.execute(
        f"""
        SELECT evidence_id, source_key, source_type, source_quality, source_status,
               published_at, ingested_at, text_excerpt, metadata_json, quality_score,
               usable_for_core_claim, usable_for_promotion
        FROM evidence_items
        WHERE {where}
        ORDER BY datetime(COALESCE(published_at, ingested_at, created_at)) DESC, id DESC
        LIMIT ?
        """,
        (*params, limit),
    ).fetchall()


def build_evidence_quality_gate(
    conn: sqlite3.Connection,
    ticker: str,
    *,
    evidence_ids: list[str] | None = None,
    theme: str | None = None,
    limit: int = 80,
) -> dict[str, Any]:
    ensure_evidence_quality_columns(conn)
    rows: list[Any]
    if evidence_ids:
        placeholders = ",".join("?" for _ in evidence_ids)
        rows = conn.execute(
            f"""
            SELECT evidence_id, source_key, source_type, source_quality, source_status,
                   published_at, ingested_at, text_excerpt, metadata_json, quality_score,
                   usable_for_core_claim, usable_for_promotion
            FROM evidence_items
            WHERE evidence_id IN ({placeholders})
            """,
            tuple(evidence_ids),
        ).fetchall()
    else:
        rows = _ticker_evidence_rows(conn, ticker, limit=limit)
    dimensions = [phase19_quality_dimensions(row, ticker=ticker, theme=theme) for row in rows]
    counts = {
        "high": sum(1 for item in dimensions if item["quality_level"] == "high"),
        "medium": sum(1 for item in dimensions if item["quality_level"] == "medium"),
        "low": sum(1 for item in dimensions if item["quality_level"] == "low"),
        "blocked": sum(1 for item in dimensions if item["quality_level"] == "blocked"),
    }
    if not dimensions:
        status = "blocked"
    elif counts["high"] >= 1:
        status = "pass_with_warnings" if counts["low"] or counts["blocked"] else "pass"
    elif counts["medium"] >= 1:
        status = "pass_with_warnings"
    else:
        status = "blocked"
    remaining = [
        {
            "evidence_id": item.get("evidence_id"),
            "issue": item.get("remaining_issue"),
            "action": "supporting_only" if item.get("quality_level") == "low" else "block_promotion",
        }
        for item in dimensions
        if item.get("remaining_issue")
    ]
    return {
        "ticker": str(ticker or "").upper(),
        "evidence_quality_gate": {
            "status": status,
            "high_quality_evidence_count": counts["high"],
            "medium_quality_evidence_count": counts["medium"],
            "low_quality_evidence_count": counts["low"],
            "blocked_evidence_count": counts["blocked"],
            "usable_for_promotion": status in {"pass", "pass_with_warnings"} and counts["high"] >= 1,
            "remaining_issues": remaining[:10],
        },
        "evidence": dimensions,
    }
