#!/usr/bin/env python3
"""Phase 6 portfolio risk helpers for candidate sizing and exposure checks."""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from datetime import datetime
from typing import Any

from smr_paper_portfolio import is_price_fresh, latest_price_info, market_for_ticker
from smr_portfolio import load_portfolio_policy, resolve_sector
from smr_phase6_watchlists import watchlist_map as load_watchlist_map


DEFAULT_PHASE6_RISK_POLICY = {
    "max_single_name_exposure_pct": 5.0,
    "max_theme_exposure_pct": 12.0,
    "max_market_exposure_pct": 18.0,
    "max_sector_exposure_pct": 12.0,
    "daily_new_position_limit": 3,
    "fresh_price_max_age_days": 7,
}


def _now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _safe_float(value: Any) -> float | None:
    if value in (None, "", "None", "nan", "-", "--"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _loads_json(raw: str | None, fallback: Any) -> Any:
    if raw in (None, ""):
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name=?", (name,)).fetchone()
    return bool(row)


def _table_columns(conn: sqlite3.Connection, name: str) -> set[str]:
    if not _table_exists(conn, name):
        return set()
    return {row[1] for row in conn.execute(f"PRAGMA table_info({name})").fetchall()}


def _position_rows(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if _table_exists(conn, "paper_portfolio_positions"):
        paper_columns = _table_columns(conn, "paper_portfolio_positions")
        ticker_col = "ticker"
        market_col = "market"
        rows.extend(
            [
                {
                    "position_source": "paper",
                    "position_id": row[0],
                    "ticker": row[1],
                    "market": row[2],
                    "quantity": row[3],
                    "avg_cost": row[4],
                    "position_pct": row[5],
                    "status": row[6],
                    "opened_at": row[7],
                    "closed_at": row[8],
                    "source_recommendation_id": row[9],
                    "metadata": _loads_json(row[10], {}),
                }
                for row in conn.execute(
                    f"""
                    SELECT position_id, {ticker_col}, {market_col}, quantity, avg_cost, position_pct,
                           status, opened_at, closed_at, source_recommendation_id, metadata_json
                    FROM paper_portfolio_positions
                    WHERE status='open'
                    ORDER BY datetime(opened_at) DESC, id DESC
                    """
                ).fetchall()
            ]
        )
    if _table_exists(conn, "position"):
        rows.extend(
            [
                {
                    "position_source": "live",
                    "position_id": f"live::{row[0]}",
                    "ticker": row[0],
                    "market": market_for_ticker(row[0]),
                    "quantity": row[3],
                    "avg_cost": row[2],
                    "position_pct": round((row[4] or 0.0) / 1_000_000 * 100.0, 3) if row[4] is not None else None,
                    "status": row[8],
                    "opened_at": row[1],
                    "closed_at": None,
                    "source_recommendation_id": None,
                    "metadata": {
                        "thesis": row[7],
                        "target_price": row[5],
                        "stop_loss": row[6],
                    },
                }
                for row in conn.execute(
                    """
                    SELECT ts_code, entry_date, entry_price, shares, cost, target_price, stop_loss, thesis, status
                    FROM position
                    WHERE status='open'
                    ORDER BY entry_date DESC, rowid DESC
                    """
                ).fetchall()
            ]
        )
    return rows


def _recommendation_metadata(conn: sqlite3.Connection, recommendation_id: str | None) -> dict[str, Any]:
    if not recommendation_id or not _table_exists(conn, "decision_ledger"):
        return {}
    row = conn.execute(
        """
        SELECT metadata_json
        FROM decision_ledger
        WHERE recommendation_id=?
        ORDER BY datetime(updated_at) DESC, id DESC
        LIMIT 1
        """,
        (recommendation_id,),
    ).fetchone()
    if not row:
        return {}
    return _loads_json(row[0], {})


def _position_context(conn: sqlite3.Connection, row: dict[str, Any], watchlist_lookup: dict[str, dict[str, Any]]) -> dict[str, Any]:
    metadata = dict(row.get("metadata") or {})
    recommendation_meta = _recommendation_metadata(conn, row.get("source_recommendation_id"))
    watchlist_item = watchlist_lookup.get(str(row.get("ticker") or "").upper()) or {}
    theme = (
        metadata.get("theme")
        or recommendation_meta.get("theme")
        or recommendation_meta.get("candidate", {}).get("theme")
        or watchlist_item.get("theme")
        or "unknown"
    )
    sector = (
        metadata.get("sector")
        or recommendation_meta.get("sector")
        or recommendation_meta.get("candidate", {}).get("sector")
        or watchlist_item.get("sector")
        or resolve_sector(conn, row.get("ticker")) or "unknown"
    )
    market = (
        row.get("market")
        or metadata.get("market")
        or recommendation_meta.get("market")
        or watchlist_item.get("market")
        or market_for_ticker(row.get("ticker"))
    )
    price_info = latest_price_info(conn, row.get("ticker"), market)
    fresh = is_price_fresh(price_info, max_age_days=int(DEFAULT_PHASE6_RISK_POLICY["fresh_price_max_age_days"]))
    latest_price = _safe_float(price_info.get("price"))
    avg_cost = _safe_float(row.get("avg_cost"))
    quantity = _safe_float(row.get("quantity")) or 0.0
    notional = None
    unrealized_pnl = None
    if latest_price is not None and avg_cost is not None and quantity:
        notional = latest_price * quantity
        if fresh:
            unrealized_pnl = (latest_price - avg_cost) * quantity
    position_pct = _safe_float(row.get("position_pct"))
    if position_pct is None and notional is not None:
        capital = float(load_portfolio_policy().get("portfolio_capital") or 1_000_000)
        position_pct = round((notional / capital) * 100.0, 4)
    return {
        **row,
        "theme": theme,
        "sector": sector,
        "market": market,
        "latest_price": latest_price,
        "latest_price_trade_date": price_info.get("trade_date"),
        "price_status": "fresh" if fresh else ("stale" if latest_price is not None else "missing"),
        "price_reason": price_info.get("reason"),
        "position_pct": position_pct,
        "notional": notional,
        "unrealized_pnl": unrealized_pnl,
        "price_fresh": fresh,
    }


def _group_exposure(rows: list[dict[str, Any]], key: str) -> dict[str, float]:
    totals: dict[str, float] = defaultdict(float)
    for row in rows:
        pct = _safe_float(row.get("position_pct")) or 0.0
        bucket = str(row.get(key) or "unknown")
        totals[bucket] += pct
    return {bucket: round(value, 4) for bucket, value in totals.items()}


def evaluate_portfolio_risk(
    conn: sqlite3.Connection,
    ticker: str,
    watchlist_item: dict[str, Any] | None = None,
    suggested_position_pct: float | None = None,
    max_position_pct: float | None = None,
    watchlist_name: str = "ai_core",
    policy: dict[str, Any] | None = None,
    watchlist_items: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    policy = {**DEFAULT_PHASE6_RISK_POLICY, **(policy or {})}
    base_policy = load_portfolio_policy()
    capital = float(base_policy.get("portfolio_capital") or 1_000_000)
    if watchlist_items is None and watchlist_name:
        try:
            watchlist_items = load_watchlist_map(watchlist_name)
        except Exception:
            watchlist_items = []
    watchlist_items = watchlist_items or []
    watchlist_lookup = {item["ticker"].upper(): item for item in watchlist_items}
    if watchlist_item:
        watchlist_lookup[str(watchlist_item.get("ticker") or ticker).upper()] = watchlist_item
    base_watchlist_item = watchlist_lookup.get(ticker.upper()) or watchlist_item or {}
    market = str(base_watchlist_item.get("market") or market_for_ticker(ticker) or "").upper() or None
    theme = str(base_watchlist_item.get("theme") or "unknown")
    sector = str(base_watchlist_item.get("sector") or resolve_sector(conn, ticker) or "unknown")
    base_suggested = _safe_float(suggested_position_pct) or _safe_float(base_watchlist_item.get("max_position_pct")) or 1.0
    base_max = _safe_float(max_position_pct) or _safe_float(base_watchlist_item.get("max_position_pct")) or base_suggested
    positions = [_position_context(conn, row, watchlist_lookup) for row in _position_rows(conn)]
    single_name_pct = sum(_safe_float(row.get("position_pct")) or 0.0 for row in positions if str(row.get("ticker") or "").upper() == ticker.upper())
    theme_pct = sum(_safe_float(row.get("position_pct")) or 0.0 for row in positions if str(row.get("theme") or "").lower() == theme.lower())
    market_pct = sum(_safe_float(row.get("position_pct")) or 0.0 for row in positions if str(row.get("market") or "").upper() == str(market or "").upper())
    sector_pct = sum(_safe_float(row.get("position_pct")) or 0.0 for row in positions if str(row.get("sector") or "").lower() == sector.lower())
    today = datetime.now().date().isoformat()
    new_position_count = sum(1 for row in positions if str(row.get("opened_at") or "")[:10] == today)
    new_position_limit = int(policy["daily_new_position_limit"])
    single_headroom = float(policy["max_single_name_exposure_pct"]) - single_name_pct
    theme_headroom = float(policy["max_theme_exposure_pct"]) - theme_pct
    market_headroom = float(policy["max_market_exposure_pct"]) - market_pct
    sector_headroom = float(policy["max_sector_exposure_pct"]) - sector_pct
    allowed_position_pct = min(
        base_suggested,
        max(0.0, single_headroom),
        max(0.0, theme_headroom),
        max(0.0, market_headroom),
        max(0.0, sector_headroom),
    )
    limiting_dimension = min(
        (
            ("single_name", single_headroom),
            ("theme", theme_headroom),
            ("market", market_headroom),
            ("sector", sector_headroom),
        ),
        key=lambda item: item[1],
    )[0]
    blocking_factors: list[dict[str, Any]] = []
    minimum_fix_path: list[str] = []
    status = "pass"
    recommended_action = "keep"
    if new_position_count >= new_position_limit:
        status = "block"
        recommended_action = "degrade"
        blocking_factors.append(
            {
                "code": "DAILY_NEW_POSITION_LIMIT",
                "severity": "blocker",
                "detail": f"{new_position_count} open positions already meet or exceed daily limit {new_position_limit}",
            }
        )
        minimum_fix_path.append("wait for existing new positions to settle before opening another one")
    if single_headroom <= 0 or theme_headroom <= 0 or market_headroom <= 0 or sector_headroom <= 0:
        status = "block"
        recommended_action = "degrade"
        if single_headroom <= 0:
            blocking_factors.append(
                {
                    "code": "SINGLE_NAME_EXPOSURE",
                    "severity": "blocker",
                    "detail": f"{ticker} single-name exposure is already at {single_name_pct:.2f}%",
                }
            )
            minimum_fix_path.append("reduce existing exposure to the ticker before adding more")
        if theme_headroom <= 0:
            blocking_factors.append(
                {
                    "code": "THEME_EXPOSURE",
                    "severity": "blocker",
                    "detail": f"theme {theme} is already at {theme_pct:.2f}%",
                }
            )
            minimum_fix_path.append("reduce the theme cluster before adding another name")
        if market_headroom <= 0:
            blocking_factors.append(
                {
                    "code": "MARKET_EXPOSURE",
                    "severity": "blocker",
                    "detail": f"market {market or 'unknown'} is already at {market_pct:.2f}%",
                }
            )
            minimum_fix_path.append("reduce same-market exposure before adding another name")
        if sector_headroom <= 0:
            blocking_factors.append(
                {
                    "code": "SECTOR_EXPOSURE",
                    "severity": "blocker",
                    "detail": f"sector {sector} is already at {sector_pct:.2f}%",
                }
            )
            minimum_fix_path.append("reduce sector exposure before adding another name")
    elif allowed_position_pct < base_suggested:
        status = "warn"
        recommended_action = "downsize"
        blocking_factors.append(
            {
                "code": "RISK_HEADROOM",
                "severity": "warn",
                "detail": f"{limiting_dimension} headroom caps the candidate at {allowed_position_pct:.2f}%",
            }
        )
        minimum_fix_path.append(f"size the new position to {allowed_position_pct:.2f}% or less")

    exposure = {
        "single_name": round(single_name_pct, 4),
        "theme": round(theme_pct, 4),
        "market": round(market_pct, 4),
        "sector": round(sector_pct, 4),
        "current_positions": len(positions),
        "daily_new_position_count": new_position_count,
    }
    projected = {
        "single_name": round(single_name_pct + base_suggested, 4),
        "theme": round(theme_pct + base_suggested, 4),
        "market": round(market_pct + base_suggested, 4),
        "sector": round(sector_pct + base_suggested, 4),
    }
    limits = {
        "single_name": float(policy["max_single_name_exposure_pct"]),
        "theme": float(policy["max_theme_exposure_pct"]),
        "market": float(policy["max_market_exposure_pct"]),
        "sector": float(policy["max_sector_exposure_pct"]),
        "daily_new_position_limit": new_position_limit,
    }
    if status == "pass" and allowed_position_pct < base_suggested:
        allowed_position_pct = round(allowed_position_pct, 4)
    elif status == "pass":
        allowed_position_pct = round(base_suggested, 4)
    else:
        allowed_position_pct = round(allowed_position_pct, 4)
    recommended_max_position_pct = round(min(base_max, allowed_position_pct if status != "block" else allowed_position_pct), 4)
    if status == "block":
        if not minimum_fix_path:
            minimum_fix_path.append("clear portfolio exposure headroom before promoting another buy/add candidate")
        if allowed_position_pct <= 0.0:
            allowed_position_pct = 0.0
            recommended_max_position_pct = 0.0
    return {
        "ticker": ticker,
        "market": market,
        "theme": theme,
        "sector": sector,
        "watchlist_id": watchlist_name,
        "watchlist_item": base_watchlist_item,
        "status": status,
        "recommended_action": recommended_action,
        "recommended_position_pct": allowed_position_pct,
        "recommended_max_position_pct": recommended_max_position_pct,
        "base_position_pct": round(base_suggested, 4),
        "base_max_position_pct": round(base_max, 4),
        "exposure": exposure,
        "projected_exposure": projected,
        "limits": limits,
        "blocking_factors": blocking_factors,
        "minimum_fix_path": minimum_fix_path,
        "position_context_count": len(positions),
        "generated_at": _now_ts(),
    }
