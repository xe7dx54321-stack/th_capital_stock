#!/usr/bin/env python3
"""Lightweight valuation snapshot v1 for report lint and context-only odds checks."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _dumps(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, sort_keys=True, default=str)


def ensure_valuation_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS valuation_snapshot (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ticker TEXT NOT NULL,
            market TEXT,
            generated_at TEXT NOT NULL,
            valuation_available INTEGER NOT NULL DEFAULT 0,
            current_price REAL,
            market_cap REAL,
            pe_ttm REAL,
            ps_ttm REAL,
            pb REAL,
            historical_percentile REAL,
            peer_comparison_json TEXT NOT NULL DEFAULT '{}',
            valuation_status TEXT NOT NULL,
            missing_data_json TEXT NOT NULL DEFAULT '[]',
            allowed_usage TEXT NOT NULL,
            metadata_json TEXT NOT NULL DEFAULT '{}'
        )
        """
    )


def market_for_ticker(ticker: str | None) -> str | None:
    text = str(ticker or "")
    if text.endswith((".SZ", ".SH", ".BJ")):
        return "A"
    if text.endswith(".HK"):
        return "H"
    if text:
        return "US"
    return None


def relation_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name=?", (name,)).fetchone()
    return bool(row)


def latest_daily_price(conn: sqlite3.Connection, ticker: str, market: str | None) -> tuple[float | None, str | None]:
    if market == "US" and relation_exists(conn, "us_daily_bar"):
        row = conn.execute(
            "SELECT close, trade_date FROM us_daily_bar WHERE ts_code=? ORDER BY trade_date DESC LIMIT 1",
            (ticker,),
        ).fetchone()
        return (float(row[0]), row[1]) if row and row[0] is not None else (None, None)
    if relation_exists(conn, "daily_bar"):
        row = conn.execute(
            "SELECT close, trade_date FROM daily_bar WHERE ts_code=? ORDER BY trade_date DESC LIMIT 1",
            (ticker,),
        ).fetchone()
        return (float(row[0]), row[1]) if row and row[0] is not None else (None, None)
    return None, None


def latest_factor(conn: sqlite3.Connection, ticker: str) -> dict[str, Any]:
    if not relation_exists(conn, "factor_daily"):
        return {}
    columns = {row[1] for row in conn.execute("PRAGMA table_info(factor_daily)").fetchall()}
    wanted = [col for col in ("pe_ttm", "ps_ttm", "pb", "total_mv", "market_cap") if col in columns]
    if not wanted:
        return {}
    row = conn.execute(
        f"SELECT {', '.join(wanted)}, trade_date FROM factor_daily WHERE ts_code=? ORDER BY trade_date DESC LIMIT 1",
        (ticker,),
    ).fetchone()
    if not row:
        return {}
    values = {wanted[index]: row[index] for index in range(len(wanted))}
    values["factor_trade_date"] = row[len(wanted)]
    return values


def build_valuation_snapshot(
    conn: sqlite3.Connection,
    ticker: str,
    data_health_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ensure_valuation_table(conn)
    market = market_for_ticker(ticker)
    current_price, price_date = latest_daily_price(conn, ticker, market)
    factor = latest_factor(conn, ticker)
    missing = []
    if current_price is None:
        missing.append("current_price")
    if "pe_ttm" not in factor:
        missing.append("pe_ttm")
    missing.extend(["forward_eps", "official_consensus", "historical_percentile", "peer_set"])
    health = data_health_snapshot or {}
    daily_rows = [
        item for item in health.get("items") or []
        if item.get("data_type") == "daily_bar" and (not market or item.get("market") in {market, "global"})
    ]
    stale_price = any(item.get("freshness_status") in {"stale", "missing"} for item in daily_rows)
    if stale_price:
        missing.append("fresh_price")
    available = bool(current_price or factor)
    valuation_status = "stale_price" if stale_price else ("partial" if available else "missing")
    allowed_usage = "context_only" if missing else "valuation_support"
    snapshot = {
        "ticker": ticker,
        "market": market,
        "generated_at": _now(),
        "valuation_available": available,
        "current_price": current_price,
        "price_trade_date": price_date,
        "market_cap": factor.get("total_mv") or factor.get("market_cap"),
        "pe_ttm": factor.get("pe_ttm"),
        "ps_ttm": factor.get("ps_ttm"),
        "pb": factor.get("pb"),
        "historical_percentile": None,
        "peer_comparison": {},
        "valuation_status": valuation_status,
        "missing_data": sorted(set(missing)),
        "allowed_usage": allowed_usage,
    }
    conn.execute(
        """
        INSERT INTO valuation_snapshot (
            ticker, market, generated_at, valuation_available, current_price, market_cap, pe_ttm,
            ps_ttm, pb, historical_percentile, peer_comparison_json, valuation_status,
            missing_data_json, allowed_usage, metadata_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ticker,
            market,
            snapshot["generated_at"],
            1 if available else 0,
            current_price,
            snapshot["market_cap"],
            snapshot["pe_ttm"],
            snapshot["ps_ttm"],
            snapshot["pb"],
            None,
            "{}",
            valuation_status,
            _dumps(snapshot["missing_data"]),
            allowed_usage,
            _dumps({"price_trade_date": price_date}),
        ),
    )
    return snapshot
