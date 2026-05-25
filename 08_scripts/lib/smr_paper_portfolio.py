#!/usr/bin/env python3
"""Paper portfolio lifecycle for approved recommendations."""

from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from typing import Any

from smr_decision import ensure_decision_tables
from smr_portfolio import load_portfolio_policy
from smr_wiki import generate_execution_id


def now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def dumps(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, sort_keys=True, default=str)


def loads(raw: str | None, fallback: Any) -> Any:
    if raw in (None, ""):
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def relation_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name=?", (name,)).fetchone()
    return bool(row)


def table_columns(conn: sqlite3.Connection, name: str) -> set[str]:
    if not relation_exists(conn, name):
        return set()
    return {row[1] for row in conn.execute(f"PRAGMA table_info({name})").fetchall()}


def ensure_paper_portfolio_tables(conn: sqlite3.Connection) -> None:
    ensure_decision_tables(conn)
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS paper_portfolio_orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT UNIQUE NOT NULL,
            recommendation_id TEXT,
            ticker TEXT,
            market TEXT,
            side TEXT,
            order_type TEXT,
            suggested_position_pct REAL,
            reference_price REAL,
            status TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            executed_at TEXT,
            metadata_json TEXT NOT NULL DEFAULT '{}'
        );

        CREATE INDEX IF NOT EXISTS idx_paper_orders_recommendation
        ON paper_portfolio_orders(recommendation_id, created_at DESC);

        CREATE TABLE IF NOT EXISTS paper_portfolio_positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            position_id TEXT UNIQUE NOT NULL,
            ticker TEXT,
            market TEXT,
            quantity REAL,
            avg_cost REAL,
            position_pct REAL,
            status TEXT,
            opened_at TEXT,
            closed_at TEXT,
            source_recommendation_id TEXT,
            metadata_json TEXT NOT NULL DEFAULT '{}'
        );

        CREATE INDEX IF NOT EXISTS idx_paper_positions_ticker_status
        ON paper_portfolio_positions(ticker, status);
        """
    )


def market_for_ticker(ticker: str | None, fallback: str | None = None) -> str | None:
    fallback_text = str(fallback or "").strip().upper()
    if fallback_text in {"A", "H", "US"}:
        return fallback_text
    text = str(ticker or "").upper()
    if text.endswith((".SZ", ".SH", ".BJ")):
        return "A"
    if text.endswith(".HK"):
        return "H"
    if text:
        return "US"
    return None


def parse_trade_date(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(text[: len(fmt)], fmt)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text[:19])
    except ValueError:
        return None


def latest_price_info(conn: sqlite3.Connection, ticker: str, market: str | None = None) -> dict[str, Any]:
    market = market_for_ticker(ticker, market)
    table = "us_daily_bar" if market == "US" else "daily_bar"
    if not relation_exists(conn, table):
        return {"price": None, "trade_date": None, "market": market, "reason": f"{table}_missing"}
    columns = table_columns(conn, table)
    ticker_column = "ts_code" if "ts_code" in columns else "symbol"
    if "close" not in columns or "trade_date" not in columns:
        return {"price": None, "trade_date": None, "market": market, "reason": f"{table}_columns_missing"}
    row = conn.execute(
        f"SELECT close, trade_date FROM {table} WHERE {ticker_column}=? ORDER BY trade_date DESC LIMIT 1",
        (ticker,),
    ).fetchone()
    if not row or row[0] is None:
        return {"price": None, "trade_date": None, "market": market, "reason": "price_missing"}
    return {"price": float(row[0]), "trade_date": row[1], "market": market, "reason": None}


def is_price_fresh(price_info: dict[str, Any], max_age_days: int = 7) -> bool:
    trade_dt = parse_trade_date(price_info.get("trade_date"))
    if not trade_dt:
        return False
    return (datetime.now().date() - trade_dt.date()).days <= max_age_days


def side_from_action(action: str | None) -> str:
    text = str(action or "").lower()
    if any(token in text for token in ("sell", "reduce", "trim", "减仓", "卖出")):
        return "sell"
    return "buy"


def order_id_for(recommendation_id: str) -> str:
    return f"paper_order__{recommendation_id}"


def existing_open_position(conn: sqlite3.Connection, ticker: str) -> dict[str, Any] | None:
    ensure_paper_portfolio_tables(conn)
    row = conn.execute(
        """
        SELECT position_id, ticker, market, quantity, avg_cost, position_pct, status,
               opened_at, metadata_json
        FROM paper_portfolio_positions
        WHERE ticker=? AND status='open'
        ORDER BY datetime(opened_at) DESC, id DESC
        LIMIT 1
        """,
        (ticker,),
    ).fetchone()
    if not row:
        return None
    return {
        "position_id": row[0],
        "ticker": row[1],
        "market": row[2],
        "quantity": row[3],
        "avg_cost": row[4],
        "position_pct": row[5],
        "status": row[6],
        "opened_at": row[7],
        "metadata": loads(row[8], {}),
    }


def approved_recommendations(conn: sqlite3.Connection, limit: int = 100) -> list[dict[str, Any]]:
    ensure_paper_portfolio_tables(conn)
    rows = conn.execute(
        """
        SELECT recommendation_id, ticker, market, action, suggested_position_pct,
               max_position_pct, metadata_json, updated_at
        FROM decision_ledger
        WHERE status='approved_paper'
          AND ticker IS NOT NULL
        ORDER BY datetime(updated_at) DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [
        {
            "recommendation_id": row[0],
            "ticker": row[1],
            "market": row[2],
            "action": row[3],
            "suggested_position_pct": row[4],
            "max_position_pct": row[5],
            "metadata": loads(row[6], {}),
            "updated_at": row[7],
        }
        for row in rows
    ]


def latest_recommendation_status(conn: sqlite3.Connection, recommendation_id: str) -> str | None:
    ensure_paper_portfolio_tables(conn)
    row = conn.execute(
        """
        SELECT status
        FROM decision_ledger
        WHERE recommendation_id=?
        ORDER BY datetime(updated_at) DESC, id DESC
        LIMIT 1
        """,
        (recommendation_id,),
    ).fetchone()
    return row[0] if row else None


def update_ledger_paper_trace(
    conn: sqlite3.Connection,
    recommendation_id: str,
    order: dict[str, Any] | None = None,
    position: dict[str, Any] | None = None,
    lifecycle_status: str | None = None,
    reason: str | None = None,
) -> None:
    ensure_paper_portfolio_tables(conn)
    row = conn.execute(
        "SELECT metadata_json FROM decision_ledger WHERE recommendation_id=? ORDER BY updated_at DESC LIMIT 1",
        (recommendation_id,),
    ).fetchone()
    metadata = loads(row[0], {}) if row else {}
    trace = metadata.get("paper_portfolio") or {}
    if order:
        trace["order_id"] = order.get("order_id")
        trace["order_status"] = order.get("status")
    if position:
        trace["position_id"] = position.get("position_id")
        trace["position_status"] = position.get("status")
    if lifecycle_status:
        trace["lifecycle_status"] = lifecycle_status
    if reason:
        trace["reason"] = reason
    trace["updated_at"] = now_ts()
    metadata["paper_portfolio"] = trace
    conn.execute(
        "UPDATE decision_ledger SET metadata_json=?, updated_at=? WHERE recommendation_id=?",
        (dumps(metadata), now_ts(), recommendation_id),
    )


def create_order_for_approved_recommendation(
    conn: sqlite3.Connection,
    recommendation: dict[str, Any],
    max_price_age_days: int = 7,
    dry_run: bool = False,
) -> dict[str, Any]:
    ensure_paper_portfolio_tables(conn)
    rec_id = recommendation["recommendation_id"]
    latest_status = latest_recommendation_status(conn, rec_id)
    if latest_status != "approved_paper":
        if not dry_run:
            update_ledger_paper_trace(
                conn,
                rec_id,
                lifecycle_status="paper_order_blocked",
                reason=f"paper order requires approved_paper status, got {latest_status or 'unknown'}",
            )
        return {
            "order_id": None,
            "status": "blocked_not_approved",
            "recommendation_id": rec_id,
            "created": False,
            "reason": "paper order requires approved_paper status",
            "current_status": latest_status,
            "dry_run": dry_run,
        }
    existing = conn.execute(
        "SELECT order_id, status FROM paper_portfolio_orders WHERE recommendation_id=? ORDER BY id DESC LIMIT 1",
        (rec_id,),
    ).fetchone()
    if existing:
        return {"order_id": existing[0], "status": existing[1], "recommendation_id": rec_id, "created": False}

    ticker = recommendation.get("ticker")
    market = market_for_ticker(ticker, recommendation.get("market"))
    side = side_from_action(recommendation.get("action"))
    price_info = latest_price_info(conn, ticker, market)
    status = "created"
    reason = None
    if price_info.get("price") is None:
        status = "blocked_missing_price"
        reason = price_info.get("reason") or "price_missing"
    elif not is_price_fresh(price_info, max_age_days=max_price_age_days):
        status = "blocked_stale_price"
        reason = "latest price is stale"
    elif side == "sell" and not existing_open_position(conn, ticker):
        status = "blocked_no_position"
        reason = "reduce/sell candidate requires an existing open paper position"

    order = {
        "order_id": order_id_for(rec_id),
        "recommendation_id": rec_id,
        "ticker": ticker,
        "market": market,
        "side": side,
        "order_type": "market_paper",
        "suggested_position_pct": recommendation.get("suggested_position_pct") or 0.0,
        "reference_price": price_info.get("price"),
        "status": status,
        "metadata": {
            "price_info": price_info,
            "source_recommendation_metadata": recommendation.get("metadata") or {},
            "reason": reason,
        },
    }
    conn.execute(
        """
        INSERT INTO paper_portfolio_orders (
            order_id, recommendation_id, ticker, market, side, order_type,
            suggested_position_pct, reference_price, status, created_at, metadata_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            order["order_id"],
            rec_id,
            ticker,
            market,
            side,
            order["order_type"],
            order["suggested_position_pct"],
            order["reference_price"],
            status,
            now_ts(),
            dumps(order["metadata"]),
        ),
    )
    update_ledger_paper_trace(conn, rec_id, order=order, lifecycle_status=status, reason=reason)
    order["created"] = True
    return order


def execute_order_to_position(conn: sqlite3.Connection, order_id: str) -> dict[str, Any]:
    ensure_paper_portfolio_tables(conn)
    row = conn.execute(
        """
        SELECT order_id, recommendation_id, ticker, market, side, suggested_position_pct,
               reference_price, status, metadata_json
        FROM paper_portfolio_orders
        WHERE order_id=?
        """,
        (order_id,),
    ).fetchone()
    if not row:
        raise ValueError(f"unknown order_id: {order_id}")
    order = {
        "order_id": row[0],
        "recommendation_id": row[1],
        "ticker": row[2],
        "market": row[3],
        "side": row[4],
        "suggested_position_pct": row[5] or 0.0,
        "reference_price": row[6],
        "status": row[7],
        "metadata": loads(row[8], {}),
    }
    if order["status"] != "created":
        return {"order_id": order_id, "status": order["status"], "executed": False, "reason": "order_not_executable"}
    if not order["reference_price"]:
        conn.execute("UPDATE paper_portfolio_orders SET status='blocked_missing_price' WHERE order_id=?", (order_id,))
        update_ledger_paper_trace(conn, order["recommendation_id"], order={**order, "status": "blocked_missing_price"}, lifecycle_status="blocked_missing_price", reason="price_missing")
        return {"order_id": order_id, "status": "blocked_missing_price", "executed": False}

    if order["side"] == "sell":
        existing = existing_open_position(conn, order["ticker"])
        if not existing:
            conn.execute("UPDATE paper_portfolio_orders SET status='blocked_no_position' WHERE order_id=?", (order_id,))
            update_ledger_paper_trace(conn, order["recommendation_id"], order={**order, "status": "blocked_no_position"}, lifecycle_status="blocked_no_position", reason="no_open_position")
            return {"order_id": order_id, "status": "blocked_no_position", "executed": False}
        conn.execute(
            "UPDATE paper_portfolio_positions SET status='closed', closed_at=? WHERE position_id=?",
            (now_ts(), existing["position_id"]),
        )
        conn.execute(
            "UPDATE paper_portfolio_orders SET status='executed', executed_at=? WHERE order_id=?",
            (now_ts(), order_id),
        )
        update_ledger_paper_trace(
            conn,
            order["recommendation_id"],
            order={**order, "status": "executed"},
            position={**existing, "status": "closed"},
            lifecycle_status="paper_position_closed",
        )
        return {"order_id": order_id, "status": "executed", "executed": True, "position_id": existing["position_id"]}

    policy = load_portfolio_policy()
    capital = float(policy.get("portfolio_capital") or 1_000_000)
    position_pct = float(order["suggested_position_pct"] or 0.0)
    notional = capital * position_pct / 100.0
    quantity = notional / float(order["reference_price"])
    position = {
        "position_id": generate_execution_id("paper_position"),
        "ticker": order["ticker"],
        "market": order["market"],
        "quantity": quantity,
        "avg_cost": float(order["reference_price"]),
        "position_pct": position_pct,
        "status": "open",
        "source_recommendation_id": order["recommendation_id"],
        "metadata": {"order_id": order_id, "notional": notional},
    }
    conn.execute(
        """
        INSERT INTO paper_portfolio_positions (
            position_id, ticker, market, quantity, avg_cost, position_pct, status,
            opened_at, source_recommendation_id, metadata_json
        )
        VALUES (?, ?, ?, ?, ?, ?, 'open', ?, ?, ?)
        """,
        (
            position["position_id"],
            position["ticker"],
            position["market"],
            position["quantity"],
            position["avg_cost"],
            position["position_pct"],
            now_ts(),
            position["source_recommendation_id"],
            dumps(position["metadata"]),
        ),
    )
    conn.execute(
        "UPDATE paper_portfolio_orders SET status='executed', executed_at=? WHERE order_id=?",
        (now_ts(), order_id),
    )
    update_ledger_paper_trace(
        conn,
        order["recommendation_id"],
        order={**order, "status": "executed"},
        position=position,
        lifecycle_status="paper_position_open",
    )
    return {"order_id": order_id, "status": "executed", "executed": True, "position_id": position["position_id"]}


def apply_approved_recommendations(
    conn: sqlite3.Connection,
    limit: int = 100,
    execute: bool = True,
    max_price_age_days: int = 7,
) -> dict[str, Any]:
    ensure_paper_portfolio_tables(conn)
    recommendations = approved_recommendations(conn, limit=limit)
    orders: list[dict[str, Any]] = []
    executions: list[dict[str, Any]] = []
    for recommendation in recommendations:
        order = create_order_for_approved_recommendation(conn, recommendation, max_price_age_days=max_price_age_days)
        orders.append(order)
        if execute and order.get("status") == "created":
            executions.append(execute_order_to_position(conn, order["order_id"]))
    return {
        "approved_seen": len(recommendations),
        "orders_created": sum(1 for item in orders if item.get("created")),
        "orders": orders,
        "executions": executions,
        "positions_opened": sum(1 for item in executions if item.get("executed") and item.get("position_id")),
    }


def mark_open_positions_to_market(conn: sqlite3.Connection) -> dict[str, Any]:
    ensure_paper_portfolio_tables(conn)
    rows = conn.execute(
        """
        SELECT position_id, ticker, market, quantity, avg_cost, metadata_json
        FROM paper_portfolio_positions
        WHERE status='open'
        ORDER BY datetime(opened_at) DESC, id DESC
        """
    ).fetchall()
    updated = 0
    skipped = 0
    for row in rows:
        position_id, ticker, market, quantity, avg_cost, metadata_raw = row
        price_info = latest_price_info(conn, ticker, market)
        if price_info.get("price") is None:
            skipped += 1
            continue
        quantity_value = float(quantity or 0.0)
        avg_cost_value = float(avg_cost or 0.0)
        latest_price = float(price_info["price"])
        pnl = (latest_price - avg_cost_value) * quantity_value
        cost = avg_cost_value * quantity_value
        metadata = loads(metadata_raw, {})
        metadata["mark_to_market"] = {
            "latest_price": latest_price,
            "latest_trade_date": price_info.get("trade_date"),
            "unrealized_pnl": pnl,
            "unrealized_pnl_pct": (pnl / cost) if cost else None,
            "updated_at": now_ts(),
        }
        conn.execute(
            "UPDATE paper_portfolio_positions SET metadata_json=? WHERE position_id=?",
            (dumps(metadata), position_id),
        )
        updated += 1
    return {"paper_positions_marked": updated, "paper_positions_skipped": skipped}
