#!/usr/bin/env python3
"""Internal consensus-revision proxy v1.

This module deliberately does not activate official consensus data. It only
creates clearly labelled proxy observations from already ingested evidence.
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


def infer_direction(text: str) -> tuple[str, float]:
    up_terms = ["上修", "上调", "提高", "超预期", "beat", "raise", "higher", "增长"]
    down_terms = ["下修", "下调", "承压", "低于预期", "miss", "cut", "lower", "恶化"]
    up = sum(text.lower().count(term.lower()) for term in up_terms)
    down = sum(text.lower().count(term.lower()) for term in down_terms)
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
    evidence_ids = evidence_ids or []
    conn.execute(
        """
        INSERT INTO consensus_revision_proxy (
            ticker, market, period, metric, proxy_direction, proxy_magnitude, confidence,
            source_evidence_ids_json, proxy_method, is_official_consensus, created_at, metadata_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
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
        ),
    )
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
        "note": "内部预期修正代理指标，不是正式卖方一致预期。",
    }
