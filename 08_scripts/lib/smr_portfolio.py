#!/usr/bin/env python3
"""Shared helpers for SMR portfolio entry and risk monitoring."""

import json
from datetime import datetime, timedelta

from smr_paths import project_path

PORTFOLIO_POLICY_PATH = project_path("00_control", "portfolio_policy.json")

from smr_universe import relation_exists

DEFAULT_POLICY = {
    "currency": "CNY",
    "portfolio_capital": 1000000,
    "max_single_position_pct": 0.25,
    "max_sector_concentration_pct": 0.50,
    "max_total_exposure_pct": 0.90,
    "max_drawdown_pct": 0.20,
    "warning_drawdown_pct": 0.15,
    "max_weekly_loss_pct": 0.08,
    "warning_weekly_loss_pct": 0.05,
    "decision_policy": {
        "buy_score_strong": 75,
        "buy_score_probe": 62,
        "buy_score_watch": 52,
        "sell_score_exit": 60,
        "sell_score_trim": 35,
        "sell_score_watch": 18,
        "default_buy_tranche_pct": 0.08,
        "cautious_buy_tranche_pct": 0.04,
        "chase_pct_threshold": 8.0,
        "pullback_pct_threshold": -5.0,
        "take_profit_pct_threshold": 10.0,
    },
}


def load_portfolio_policy():
    if not PORTFOLIO_POLICY_PATH.exists():
        return DEFAULT_POLICY.copy()

    data = json.loads(PORTFOLIO_POLICY_PATH.read_text(encoding="utf-8"))
    policy = DEFAULT_POLICY.copy()
    policy.update(data)
    decision_policy = (DEFAULT_POLICY.get("decision_policy") or {}).copy()
    decision_policy.update((data.get("decision_policy") or {}))
    policy["decision_policy"] = decision_policy
    return policy


def latest_price(conn, ts_code):
    row = conn.execute(
        "SELECT close FROM daily_bar WHERE ts_code=? ORDER BY trade_date DESC LIMIT 1",
        (ts_code,),
    ).fetchone()
    return row[0] if row else None


def current_open_positions(conn):
    return conn.execute(
        """
        SELECT ts_code, entry_date, entry_price, shares, cost, target_price, stop_loss, thesis, pnl, pnl_pct
        FROM position
        WHERE status='open'
        """
    ).fetchall()


def has_unacknowledged_critical_alert(conn):
    row = conn.execute(
        """
        SELECT count(*)
        FROM risk_alert
        WHERE severity='critical' AND acknowledged=0
        """
    ).fetchone()
    return (row[0] or 0) > 0


def resolve_sector(conn, ts_code):
    if not relation_exists(conn, "stock_pool_latest"):
        return None
    row = conn.execute(
        """
        SELECT sector
        FROM stock_pool_latest
        WHERE ts_code=?
        ORDER BY
            CASE pool_type
                WHEN 'recommended' THEN 4
                WHEN 'candidate' THEN 3
                WHEN 'watchlist' THEN 2
                WHEN 'portfolio_seed' THEN 1
                WHEN 'seed' THEN 1
                ELSE 0
            END DESC,
            datetime(added_date) DESC
        LIMIT 1
        """,
        (ts_code,),
    ).fetchone()
    return row[0] if row else None


def latest_recommendation(conn, ts_code):
    if not relation_exists(conn, "research_decision_latest"):
        return None
    row = conn.execute(
        """
        SELECT report_id, thesis_strength, reason
        FROM research_decision_latest
        WHERE ts_code=? AND suggested_pool='recommended'
        """,
        (ts_code,),
    ).fetchone()
    if not row:
        return None
    return {"report_id": row[0], "thesis_strength": row[1], "reason": row[2]}


def recommended_in_current_pool(conn, ts_code):
    if not relation_exists(conn, "stock_pool_current"):
        return False
    row = conn.execute(
        """
        SELECT 1
        FROM stock_pool_current
        WHERE pool_type='recommended' AND ts_code=?
        """,
        (ts_code,),
    ).fetchone()
    return bool(row)


def projected_costs_by_sector(conn, extra_ts_code=None, extra_cost=0.0):
    costs = {}
    for ts_code, _entry_date, _entry_price, _shares, cost, _target_price, _stop_loss, _thesis, _pnl, _pnl_pct in current_open_positions(conn):
        sector = resolve_sector(conn, ts_code) or "unknown"
        costs[sector] = costs.get(sector, 0.0) + (cost or 0.0)

    if extra_ts_code and extra_cost:
        sector = resolve_sector(conn, extra_ts_code) or "unknown"
        costs[sector] = costs.get(sector, 0.0) + extra_cost

    return costs


def projected_total_cost(conn, extra_cost=0.0):
    total = sum((row[4] or 0.0) for row in current_open_positions(conn))
    return total + extra_cost


def weekly_loss_snapshot(conn):
    cutoff = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
    rows = conn.execute(
        """
        SELECT ts_code, entry_date, cost, pnl
        FROM position
        WHERE status='open' AND entry_date >= ?
        """,
        (cutoff,),
    ).fetchall()
    loss = 0.0
    cost_base = 0.0
    for _ts_code, _entry_date, cost, pnl in rows:
        cost_base += cost or 0.0
        if (pnl or 0.0) < 0:
            loss += abs(pnl or 0.0)
    return {"loss": loss, "cost_base": cost_base, "positions": len(rows)}
