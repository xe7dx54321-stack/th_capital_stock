#!/usr/bin/env python3
"""Lightweight valuation snapshot v2 for promotion-aware research checks."""

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
    columns = {row[1] for row in conn.execute("PRAGMA table_info(valuation_snapshot)").fetchall()}
    additions = {
        "ev_ebitda_ttm": "REAL",
        "historical_percentile_1y": "REAL",
        "historical_percentile_3y": "REAL",
        "historical_percentile_5y": "REAL",
        "peer_set_json": "TEXT NOT NULL DEFAULT '[]'",
        "peer_percentile": "REAL",
        "broker_target_price": "REAL",
        "broker_forward_eps_proxy": "REAL",
        "valuation_confidence": "REAL",
    }
    for column, ddl in additions.items():
        if column not in columns:
            conn.execute(f"ALTER TABLE valuation_snapshot ADD COLUMN {column} {ddl}")


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


def table_columns(conn: sqlite3.Connection, name: str) -> set[str]:
    if not relation_exists(conn, name):
        return set()
    return {row[1] for row in conn.execute(f"PRAGMA table_info({name})").fetchall()}


def latest_daily_price(conn: sqlite3.Connection, ticker: str, market: str | None) -> tuple[float | None, str | None]:
    if market == "US" and relation_exists(conn, "us_daily_bar"):
        columns = table_columns(conn, "us_daily_bar")
        ticker_column = "ts_code" if "ts_code" in columns else "symbol"
        row = conn.execute(
            f"SELECT close, trade_date FROM us_daily_bar WHERE {ticker_column}=? ORDER BY trade_date DESC LIMIT 1",
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
    columns = table_columns(conn, "factor_daily")
    wanted = [col for col in ("pe_ttm", "ps_ttm", "pb", "total_mv", "market_cap", "ev_ebitda_ttm") if col in columns]
    if wanted:
        row = conn.execute(
            f"SELECT {', '.join(wanted)}, trade_date FROM factor_daily WHERE ts_code=? ORDER BY trade_date DESC LIMIT 1",
            (ticker,),
        ).fetchone()
        if not row:
            return {}
        values = {wanted[index]: row[index] for index in range(len(wanted))}
        values["factor_trade_date"] = row[len(wanted)]
        return values
    if {"factor_name", "factor_value", "trade_date", "ts_code"}.issubset(columns):
        rows = conn.execute(
            """
            SELECT factor_name, factor_value, trade_date
            FROM factor_daily
            WHERE ts_code=?
            ORDER BY trade_date DESC
            """,
            (ticker,),
        ).fetchall()
        if not rows:
            return {}
        latest_date = rows[0][2]
        values = {"factor_trade_date": latest_date}
        for name, value, trade_date in rows:
            if trade_date != latest_date:
                continue
            key = str(name or "").lower()
            if key in {"pe_ttm", "ps_ttm", "pb", "total_mv", "market_cap", "ev_ebitda_ttm"}:
                values[key] = value
        return values
    return {}


def _daily_rows_for_market(health: dict[str, Any], market: str | None) -> list[dict[str, Any]]:
    return [
        item for item in health.get("items") or []
        if item.get("data_type") == "daily_bar" and (not market or item.get("market") in {market, "global"})
    ]


def build_valuation_snapshot(
    conn: sqlite3.Connection,
    ticker: str,
    data_health_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ensure_valuation_table(conn)
    market = market_for_ticker(ticker)
    current_price, price_date = latest_daily_price(conn, ticker, market)
    factor = latest_factor(conn, ticker)
    health = data_health_snapshot or {}
    daily_rows = _daily_rows_for_market(health, market)
    stale_price = any(item.get("freshness_status") in {"stale", "missing"} for item in daily_rows)

    missing = []
    if current_price is None:
        missing.append("current_price")
    if "pe_ttm" not in factor:
        missing.append("pe_ttm")
    if "ps_ttm" not in factor:
        missing.append("ps_ttm")
    if "pb" not in factor:
        missing.append("pb")
    missing.extend(["forward_eps", "official_consensus", "historical_percentile", "peer_set"])
    if stale_price:
        missing.append("fresh_price")

    available = bool(current_price is not None or factor)
    has_basic_multiple = any(factor.get(key) is not None for key in ("pe_ttm", "ps_ttm", "pb"))
    peer_comparison: dict[str, Any] = {}
    peer_set: list[str] = []
    broker_forward_eps_proxy = None
    valuation_confidence = 0.0
    if current_price is not None:
        valuation_confidence += 0.25
    if has_basic_multiple:
        valuation_confidence += 0.3
    if peer_set:
        valuation_confidence += 0.2
    if broker_forward_eps_proxy:
        valuation_confidence += 0.25

    if stale_price:
        valuation_status = "stale_price"
        allowed_usage = "blocked_due_to_stale_price"
    elif broker_forward_eps_proxy and peer_set:
        valuation_status = "promotion_ready"
        allowed_usage = "promotion_eligible"
    elif available and (current_price is not None or has_basic_multiple):
        valuation_status = "partial"
        allowed_usage = "supporting_evidence"
    else:
        valuation_status = "missing"
        allowed_usage = "context_only"

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
        "ev_ebitda_ttm": factor.get("ev_ebitda_ttm"),
        "historical_percentile": None,
        "historical_percentile_1y": None,
        "historical_percentile_3y": None,
        "historical_percentile_5y": None,
        "peer_comparison": peer_comparison,
        "peer_set": peer_set,
        "peer_percentile": None,
        "broker_target_price": None,
        "broker_forward_eps_proxy": broker_forward_eps_proxy,
        "valuation_confidence": round(valuation_confidence, 2),
        "valuation_status": valuation_status,
        "missing_data": sorted(set(missing)),
        "allowed_usage": allowed_usage,
    }
    conn.execute(
        """
        INSERT INTO valuation_snapshot (
            ticker, market, generated_at, valuation_available, current_price, market_cap, pe_ttm,
            ps_ttm, pb, historical_percentile, peer_comparison_json, valuation_status,
            missing_data_json, allowed_usage, metadata_json, ev_ebitda_ttm,
            historical_percentile_1y, historical_percentile_3y, historical_percentile_5y,
            peer_set_json, peer_percentile, broker_target_price, broker_forward_eps_proxy,
            valuation_confidence
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
            _dumps(peer_comparison),
            valuation_status,
            _dumps(snapshot["missing_data"]),
            allowed_usage,
            _dumps({"price_trade_date": price_date, "factor_trade_date": factor.get("factor_trade_date")}),
            snapshot["ev_ebitda_ttm"],
            None,
            None,
            None,
            _dumps(peer_set),
            None,
            None,
            broker_forward_eps_proxy,
            snapshot["valuation_confidence"],
        ),
    )
    return snapshot
