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
    if any(token in clean.lower() for token in ("revenue", "eps", "cash", "margin", "guidance", "risk", "profit")):
        score += 0.2
    if any(token in clean for token in ("收入", "利润", "现金流", "毛利率", "风险", "指引")):
        score += 0.15
    return min(score, 1.0)


def directness_for(score: float) -> str:
    if score >= 0.75:
        return "high"
    if score >= 0.5:
        return "medium"
    return "low"


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
    directness_value = (ticker_score * 0.45) + (specificity * 0.4) + (theme_score * 0.15)
    score = (base * 0.46 + recency * 0.18 + ticker_score * 0.16 + specificity * 0.14 + theme_score * 0.06) * status_mult
    if source_type in {"filing", "fundamentals"}:
        score += 0.04
    quality_score = round(max(0.0, min(score, 1.0)), 3)
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
        "usable_for_core_claim": usable_for_core,
        "usable_for_promotion": usable_for_promotion,
        "metadata": {
            "source_quality": source_quality,
            "source_type": source_type,
            "source_status_multiplier": status_mult,
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
