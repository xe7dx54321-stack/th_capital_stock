#!/usr/bin/env python3
"""Internal consensus-revision proxy.

This module deliberately does not activate official consensus data. It creates
clearly labelled internal proxy observations from already ingested evidence and
exposes a quality grade that promotion rules can use conservatively.
"""

from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime
from typing import Any


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _dumps(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, sort_keys=True, default=str)


def ensure_consensus_proxy_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS consensus_revision_proxy (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            market TEXT,
            period TEXT,
            metric TEXT,
            proxy_direction TEXT,
            proxy_magnitude REAL,
            confidence REAL,
            source_evidence_ids_json TEXT NOT NULL DEFAULT '[]',
            proxy_method TEXT,
            is_official_consensus INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            metadata_json TEXT NOT NULL DEFAULT '{}'
        )
        """
    )
    columns = {row[1] for row in conn.execute("PRAGMA table_info(consensus_revision_proxy)").fetchall()}
    additions = {
        "previous_value": "REAL",
        "current_value": "REAL",
        "revision_pct": "REAL",
        "revision_window_days": "INTEGER",
        "evidence_count": "INTEGER",
        "independent_source_count": "INTEGER",
        "proxy_quality": "TEXT",
        "usable_for_promotion": "INTEGER NOT NULL DEFAULT 0",
    }
    for column, ddl in additions.items():
        if column not in columns:
            conn.execute(f"ALTER TABLE consensus_revision_proxy ADD COLUMN {column} {ddl}")


def infer_direction(text: str) -> tuple[str, float]:
    up_terms = [
        "上修", "上调", "提高", "超预期", "beat", "raise", "raised", "higher", "增长", "upgrade",
        "涓婁慨", "涓婅皟", "鎻愰珮", "瓒呴", "澧為暱",
    ]
    down_terms = [
        "下修", "下调", "低于预期", "miss", "cut", "lower", "降低", "恶化", "downgrade",
        "涓嬩慨", "涓嬭皟", "浣庝簬", "鎭跺寲",
    ]
    lower = text.lower()
    up = sum(lower.count(term.lower()) for term in up_terms)
    down = sum(lower.count(term.lower()) for term in down_terms)
    if up > down:
        return "up", min(0.35 + up * 0.08, 0.72)
    if down > up:
        return "down", min(0.35 + down * 0.08, 0.72)
    return "unknown", 0.25


def extract_ticker(text: str, fallback: str | None = None) -> tuple[str, str | None]:
    if fallback:
        ticker = fallback
        if ticker.endswith((".SZ", ".SH", ".BJ")):
            return ticker, "A"
        if ticker.endswith(".HK"):
            return ticker, "H"
        return ticker, "US"
    match = re.search(r"([0-9]{6}\.(?:SZ|SH|BJ)|[0-9]{5}\.HK|[A-Z]{1,6})", text)
    ticker = match.group(1) if match else fallback
    if not ticker:
        return "UNKNOWN", None
    if ticker.endswith((".SZ", ".SH", ".BJ")):
        return ticker, "A"
    if ticker.endswith(".HK"):
        return ticker, "H"
    return ticker, "US"


def parse_numeric_pair(text: str) -> tuple[float | None, float | None, float | None]:
    """Extract a simple previous/current pair such as EPS 1.20 -> 1.35."""
    match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*(?:->|到|至|from)\s*([0-9]+(?:\.[0-9]+)?)", text, re.I)
    if not match:
        return None, None, None
    previous = float(match.group(1))
    current = float(match.group(2))
    revision_pct = (current - previous) / abs(previous) if previous else None
    return previous, current, revision_pct


def source_count_for_evidence(conn: sqlite3.Connection, evidence_ids: list[str]) -> int:
    if not evidence_ids:
        return 0
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name='evidence_items'"
    ).fetchone()
    if not row:
        return 0
    placeholders = ",".join("?" for _ in evidence_ids)
    rows = conn.execute(
        f"SELECT DISTINCT source_key FROM evidence_items WHERE evidence_id IN ({placeholders})",
        tuple(evidence_ids),
    ).fetchall()
    return len({item[0] for item in rows if item[0]})


def method_weight(method: str) -> float:
    value = str(method or "").strip().lower()
    if value in {"guidance_change", "earnings_surprise"}:
        return 0.28
    if value in {"direct_demand_evidence", "order_customer_evidence"}:
        return 0.24
    if value in {"broker_report_extraction", "target_price_revision"}:
        return 0.18
    if value in {"price_reaction_proxy", "news_language_proxy"}:
        return 0.08
    if value == "manual_seed":
        return 0.12
    return 0.1


def classify_proxy_quality(
    direction: str,
    confidence: float,
    evidence_count: int,
    independent_source_count: int,
    method: str,
) -> tuple[str, bool]:
    if direction not in {"up", "down"}:
        return "invalid", False
    score = confidence + method_weight(method)
    if evidence_count >= 2:
        score += 0.08
    if independent_source_count >= 2:
        score += 0.08
    if score >= 0.78 and evidence_count >= 1:
        return "strong", True
    if score >= 0.58:
        return "medium", False
    return "weak", False


def build_consensus_revision_proxy(
    conn: sqlite3.Connection,
    text: str | None,
    evidence_ids: list[str] | None = None,
    ticker: str | None = None,
    method: str = "broker_report_extraction",
) -> dict[str, Any]:
    ensure_consensus_proxy_table(conn)
    raw = str(text or "")
    detected_ticker, market = extract_ticker(raw, ticker)
    direction, confidence = infer_direction(raw)
    metric = "earnings_expectation_proxy"
    period_match = re.search(r"(20[2-9][0-9]E?|FY20[2-9][0-9]|[0-9]{4}年)", raw)
    period = period_match.group(1) if period_match else None
    evidence_ids = list(dict.fromkeys(evidence_ids or []))
    evidence_count = len(evidence_ids)
    independent_source_count = source_count_for_evidence(conn, evidence_ids)
    if evidence_count and independent_source_count == 0:
        independent_source_count = 1
    previous_value, current_value, revision_pct = parse_numeric_pair(raw)
    proxy_quality, usable_for_promotion = classify_proxy_quality(
        direction,
        confidence,
        evidence_count,
        independent_source_count,
        method,
    )
    conn.execute(
        """
        INSERT INTO consensus_revision_proxy (
            ticker, market, period, metric, proxy_direction, proxy_magnitude, confidence,
            source_evidence_ids_json, proxy_method, is_official_consensus, created_at, metadata_json,
            previous_value, current_value, revision_pct, revision_window_days, evidence_count,
            independent_source_count, proxy_quality, usable_for_promotion
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            detected_ticker,
            market,
            period,
            metric,
            direction,
            None,
            confidence,
            _dumps(evidence_ids),
            method,
            _now(),
            _dumps(
                {
                    "note": "internal consensus revision proxy only; not official sell-side consensus",
                    "raw_excerpt": raw[:500],
                }
            ),
            previous_value,
            current_value,
            revision_pct,
            30,
            evidence_count,
            independent_source_count,
            proxy_quality,
            1 if usable_for_promotion else 0,
        ),
    )
    proxy_metadata = {
        "note": "internal consensus revision proxy only; not official sell-side consensus",
        "raw_excerpt": raw[:500],
        "evidence_count": evidence_count,
        "independent_source_count": independent_source_count,
        "proxy_quality": proxy_quality,
        "usable_for_promotion": usable_for_promotion,
        "revision_window_days": 30,
        "proxy_method": method,
    }
    return {
        "ticker": detected_ticker,
        "market": market,
        "period": period,
        "metric": metric,
        "proxy_direction": direction,
        "confidence": confidence,
        "is_official_consensus": False,
        "evidence_ids": evidence_ids,
        "proxy_method": method,
        "previous_value": previous_value,
        "current_value": current_value,
        "revision_pct": revision_pct,
        "revision_window_days": 30,
        "evidence_count": evidence_count,
        "independent_source_count": independent_source_count,
        "proxy_quality": proxy_quality,
        "usable_for_promotion": usable_for_promotion,
        "proxy_metadata": proxy_metadata,
        "note": "internal consensus revision proxy only; not official sell-side consensus",
    }
