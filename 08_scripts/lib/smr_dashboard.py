#!/usr/bin/env python3
"""Shared state loaders for the SMR control tower."""

from __future__ import annotations

import hashlib
import json
import sqlite3
from collections import Counter, deque
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from smr_external_research import latest_external_research_snapshot
from smr_flow_event_digest import build_capital_flow_fact_sheet_from_payloads
from smr_official_materials import summarize_official_materials
from smr_paths import ROOT, env_or_project_path, normalize_project_path, relative_to_project
from smr_public_transcripts import latest_public_transcript_snapshot
from smr_trade_calendar import expected_trade_dates, format_date, parse_date, trade_day_lag

DB_PATH = env_or_project_path("SMR_DB_PATH", "01_data", "db", "smr.db")
RUN_LOG_PATH = env_or_project_path("SMR_RUN_LOG_PATH", "10_logs", "script_runs.jsonl")
SCHEDULER_RUN_ROOT = env_or_project_path("SMR_SCHEDULER_RUN_ROOT", "10_logs", "scheduler", "runs")

KEY_ENTITY_TYPES = [
    "daily_report_candidate",
    "daily_reporting_snapshot",
    "market_flow_anomaly_snapshot",
    "opportunity_radar_snapshot",
    "opportunity_lifecycle_snapshot",
    "strategy_evidence_snapshot",
    "thesis_attack_defense_snapshot",
    "paper_trade_watchlist_snapshot",
    "paper_watch_performance_snapshot",
    "deep_market_analysis_snapshot",
    "price_range_forecast_snapshot",
    "execution_precheck_snapshot",
    "strategy_watch_batch",
    "rotation_candidate_snapshot",
    "rotation_execution_plan_snapshot",
    "portfolio_action_memo_snapshot",
    "risk_monitor_snapshot",
    "trade_risk_decision_snapshot",
    "market_event_snapshot",
    "event_calendar_snapshot",
    "upcoming_event_calendar_snapshot",
    "margin_balance_snapshot",
    "stock_connect_flow_snapshot",
    "input_source_registry_snapshot",
]


def load_json(raw_value: str | None, default: Any) -> Any:
    if raw_value in (None, ""):
        return default
    try:
        return json.loads(raw_value)
    except json.JSONDecodeError:
        return default


def connect_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def resolve_project_path(path_value: str | None) -> Path | None:
    normalized = normalize_project_path(path_value)
    if normalized is None:
        return None
    try:
        normalized.relative_to(ROOT)
    except ValueError:
        return None
    return normalized


def path_timestamp(path: Path | None) -> str | None:
    if path is None or not path.exists():
        return None
    return datetime.fromtimestamp(path.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")


def read_text_preview(path: Path | None, max_lines: int = 12, max_chars: int = 1600) -> str | None:
    if path is None or not path.exists() or not path.is_file():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        text = path.read_text(encoding="utf-8", errors="replace")
    lines = []
    total_chars = 0
    for raw_line in text.splitlines():
        lines.append(raw_line)
        total_chars += len(raw_line)
        if len(lines) >= max_lines or total_chars >= max_chars:
            break
    preview = "\n".join(lines).strip()
    if not preview:
        return None
    if len(text) > len(preview):
        preview = f"{preview}\n..."
    return preview


def build_artifact(rel_path: str | None, label: str, summary: str | None = None) -> dict[str, Any] | None:
    if rel_path in (None, ""):
        return None
    path = resolve_project_path(rel_path)
    return {
        "label": label,
        "rel_path": relative_to_project(path) if path else rel_path,
        "abs_path": str(path) if path else None,
        "exists": bool(path and path.exists()),
        "updated_at": path_timestamp(path),
        "summary": summary,
        "preview": read_text_preview(path),
    }


def snapshot_from_row(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    relationships = load_json(row["relationships_json"], {})
    payload = load_json(row["payload_json"], {})
    return {
        "id": row["id"],
        "entity_type": row["entity_type"],
        "entity_id": row["entity_id"],
        "status": row["status"],
        "source": row["source"],
        "created_at": row["created_at"],
        "relationships": relationships,
        "payload": payload,
    }


def latest_snapshot(conn: sqlite3.Connection, entity_type: str) -> dict[str, Any] | None:
    row = conn.execute(
        """
        SELECT id, entity_type, entity_id, status, source, relationships_json, payload_json, created_at
        FROM task_registry_entity_latest
        WHERE entity_type=?
        ORDER BY datetime(created_at) DESC, snapshot_index DESC, id DESC
        LIMIT 1
        """,
        (entity_type,),
    ).fetchone()
    return snapshot_from_row(row)


def latest_snapshot_for_entity(conn: sqlite3.Connection, entity_type: str, entity_id: str | None) -> dict[str, Any] | None:
    if not entity_id:
        return None
    row = conn.execute(
        """
        SELECT id, entity_type, entity_id, status, source, relationships_json, payload_json, created_at
        FROM task_registry_entity_latest
        WHERE entity_type=? AND entity_id=?
        ORDER BY datetime(created_at) DESC, snapshot_index DESC, id DESC
        LIMIT 1
        """,
        (entity_type, entity_id),
    ).fetchone()
    return snapshot_from_row(row)


def latest_trade_dates(conn: sqlite3.Connection) -> dict[str, str | None]:
    a_share = conn.execute("SELECT MAX(trade_date) FROM daily_bar WHERE market='A'").fetchone()[0]
    hk = conn.execute("SELECT MAX(trade_date) FROM daily_bar WHERE market='H'").fetchone()[0]
    us = conn.execute("SELECT MAX(trade_date) FROM us_daily_bar").fetchone()[0]
    return {
        "a_share_latest": a_share,
        "hk_latest": hk,
        "us_latest": us,
    }


def pool_counts(conn: sqlite3.Connection) -> dict[str, int]:
    rows = conn.execute(
        """
        SELECT pool_type, COUNT(*) AS count
        FROM stock_pool_current
        GROUP BY pool_type
        ORDER BY pool_type
        """
    ).fetchall()
    return {row["pool_type"]: row["count"] for row in rows}


def open_position_summary(conn: sqlite3.Connection) -> dict[str, Any]:
    open_count = conn.execute("SELECT COUNT(*) FROM position WHERE status='open'").fetchone()[0]
    rows = conn.execute(
        """
        SELECT ts_code, entry_date, entry_price, shares, cost, pnl, pnl_pct
        FROM position
        WHERE status='open'
        ORDER BY entry_date DESC, ts_code
        LIMIT 10
        """
    ).fetchall()
    positions = []
    for row in rows:
        positions.append(
            {
                "ts_code": row["ts_code"],
                "entry_date": row["entry_date"],
                "entry_price": row["entry_price"],
                "shares": row["shares"],
                "cost": row["cost"],
                "pnl": row["pnl"],
                "pnl_pct": row["pnl_pct"],
            }
        )
    return {
        "open_count": open_count,
        "positions": positions,
    }


def risk_summary(conn: sqlite3.Connection) -> dict[str, Any]:
    counts = {}
    rows = conn.execute(
        """
        SELECT severity, COUNT(*) AS count, SUM(CASE WHEN acknowledged=0 THEN 1 ELSE 0 END) AS unacked
        FROM risk_alert
        GROUP BY severity
        ORDER BY severity
        """
    ).fetchall()
    total_alerts = 0
    unacknowledged = 0
    for row in rows:
        severity = row["severity"] or "unknown"
        counts[severity] = {
            "count": row["count"],
            "unacknowledged": row["unacked"] or 0,
        }
        total_alerts += row["count"]
        unacknowledged += row["unacked"] or 0

    recent_rows = conn.execute(
        """
        SELECT severity, alert_type, ts_code, message, action, alert_time, acknowledged
        FROM risk_alert
        ORDER BY datetime(alert_time) DESC, alert_id DESC
        LIMIT 12
        """
    ).fetchall()
    recent_alerts = []
    for row in recent_rows:
        recent_alerts.append(
            {
                "severity": row["severity"],
                "alert_type": row["alert_type"],
                "ts_code": row["ts_code"],
                "message": row["message"],
                "action": row["action"],
                "alert_time": row["alert_time"],
                "acknowledged": bool(row["acknowledged"]),
            }
        )
    return {
        "total_alerts": total_alerts,
        "unacknowledged_alerts": unacknowledged,
        "severity_counts": counts,
        "recent_alerts": recent_alerts,
    }


def recent_risk_alerts_for_symbols(
    conn: sqlite3.Connection, symbols: list[str], limit_per_symbol: int = 3
) -> dict[str, list[dict[str, Any]]]:
    if not symbols:
        return {}
    placeholders = ",".join("?" for _ in symbols)
    rows = conn.execute(
        f"""
        WITH ranked AS (
            SELECT
                severity,
                alert_type,
                ts_code,
                message,
                action,
                alert_time,
                acknowledged,
                ROW_NUMBER() OVER (
                    PARTITION BY ts_code
                    ORDER BY datetime(alert_time) DESC, alert_id DESC
                ) AS rn
            FROM risk_alert
            WHERE ts_code IN ({placeholders})
        )
        SELECT severity, alert_type, ts_code, message, action, alert_time, acknowledged
        FROM ranked
        WHERE rn <= ?
        ORDER BY ts_code, datetime(alert_time) DESC
        """,
        (*symbols, limit_per_symbol),
    ).fetchall()
    grouped = {symbol: [] for symbol in symbols}
    for row in rows:
        grouped.setdefault(row["ts_code"], []).append(
            {
                "severity": row["severity"],
                "alert_type": row["alert_type"],
                "ts_code": row["ts_code"],
                "message": row["message"],
                "action": row["action"],
                "alert_time": row["alert_time"],
                "acknowledged": bool(row["acknowledged"]),
            }
        )
    return grouped


def recent_market_events(conn: sqlite3.Connection, limit: int = 12) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT event_date, importance, event_family, event_type, entity_id, title, source_rel_path, publish_time, created_at
        FROM market_event_latest
        ORDER BY datetime(COALESCE(publish_time, created_at)) DESC, event_id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    events = []
    for row in rows:
        events.append(
            {
                "event_date": row["event_date"],
                "importance": row["importance"],
                "event_family": row["event_family"],
                "event_type": row["event_type"],
                "entity_id": row["entity_id"],
                "title": row["title"],
                "source_rel_path": row["source_rel_path"],
                "publish_time": row["publish_time"] or row["created_at"],
            }
        )
    return events


def recent_market_events_by_family(conn: sqlite3.Connection, limit_per_family: int = 6) -> dict[str, list[dict[str, Any]]]:
    families = ("announcement", "research", "news")
    grouped = {}
    for family in families:
        rows = conn.execute(
            """
            SELECT event_date, importance, event_family, event_type, entity_id, title, source_rel_path, publish_time, created_at
            FROM market_event_latest
            WHERE event_family=?
            ORDER BY datetime(COALESCE(publish_time, created_at)) DESC, event_id DESC
            LIMIT ?
            """,
            (family, limit_per_family),
        ).fetchall()
        grouped[family] = [
            {
                "event_date": row["event_date"],
                "importance": row["importance"],
                "event_family": row["event_family"],
                "event_type": row["event_type"],
                "entity_id": row["entity_id"],
                "title": row["title"],
                "source_rel_path": row["source_rel_path"],
                "publish_time": row["publish_time"] or row["created_at"],
            }
            for row in rows
        ]
    return grouped


def upcoming_market_events(conn: sqlite3.Connection, limit: int = 12) -> list[dict[str, Any]]:
    today = datetime.now().strftime("%Y-%m-%d")
    rows = conn.execute(
        """
        SELECT event_date, importance, event_family, event_type, entity_id, title, source_rel_path, publish_time, created_at, payload_json
        FROM market_event
        WHERE event_family='calendar'
          AND COALESCE(event_date, '9999-12-31') >= ?
        ORDER BY event_date ASC, datetime(COALESCE(publish_time, created_at)) DESC, event_id DESC
        LIMIT ?
        """,
        (today, limit),
    ).fetchall()
    events = []
    for row in rows:
        payload = load_json(row["payload_json"], {})
        events.append(
            {
                "event_date": row["event_date"],
                "importance": row["importance"],
                "event_family": row["event_family"],
                "event_type": row["event_type"],
                "entity_id": row["entity_id"],
                "title": row["title"],
                "source_rel_path": row["source_rel_path"],
                "publish_time": row["publish_time"] or row["created_at"],
                "calendar_kind": payload.get("calendar_kind"),
                "summary": payload.get("summary"),
                "event_time_text": payload.get("event_time_text"),
            }
        )
    return events


def recent_market_events_for_symbols(
    conn: sqlite3.Connection, symbols: list[str], limit_per_symbol: int = 4
) -> dict[str, list[dict[str, Any]]]:
    if not symbols:
        return {}
    placeholders = ",".join("?" for _ in symbols)
    rows = conn.execute(
        f"""
        WITH ranked AS (
            SELECT
                event_date,
                importance,
                event_family,
                event_type,
                entity_id,
                title,
                source_rel_path,
                publish_time,
                created_at,
                ROW_NUMBER() OVER (
                    PARTITION BY entity_id
                    ORDER BY datetime(COALESCE(publish_time, created_at)) DESC, event_id DESC
                ) AS rn
            FROM market_event_latest
            WHERE entity_id IN ({placeholders})
        )
        SELECT
            event_date,
            importance,
            event_family,
            event_type,
            entity_id,
            title,
            source_rel_path,
            publish_time,
            created_at
        FROM ranked
        WHERE rn <= ?
        ORDER BY entity_id, datetime(COALESCE(publish_time, created_at)) DESC
        """,
        (*symbols, limit_per_symbol),
    ).fetchall()
    grouped = {symbol: [] for symbol in symbols}
    for row in rows:
        grouped.setdefault(row["entity_id"], []).append(
            {
                "event_date": row["event_date"],
                "importance": row["importance"],
                "event_family": row["event_family"],
                "event_type": row["event_type"],
                "entity_id": row["entity_id"],
                "title": row["title"],
                "source_rel_path": row["source_rel_path"],
                "publish_time": row["publish_time"] or row["created_at"],
            }
        )
    return grouped


def upcoming_market_events_for_symbols(
    conn: sqlite3.Connection, symbols: list[str], limit_per_symbol: int = 3
) -> dict[str, list[dict[str, Any]]]:
    if not symbols:
        return {}
    placeholders = ",".join("?" for _ in symbols)
    today = datetime.now().strftime("%Y-%m-%d")
    rows = conn.execute(
        f"""
        WITH ranked AS (
            SELECT
                event_date,
                importance,
                event_family,
                event_type,
                entity_id,
                title,
                source_rel_path,
                publish_time,
                created_at,
                payload_json,
                ROW_NUMBER() OVER (
                    PARTITION BY entity_id
                    ORDER BY event_date ASC, datetime(COALESCE(publish_time, created_at)) DESC, event_id DESC
                ) AS rn
            FROM market_event
            WHERE entity_id IN ({placeholders})
              AND event_family='calendar'
              AND COALESCE(event_date, '9999-12-31') >= ?
        )
        SELECT
            event_date,
            importance,
            event_family,
            event_type,
            entity_id,
            title,
            source_rel_path,
            publish_time,
            created_at,
            payload_json
        FROM ranked
        WHERE rn <= ?
        ORDER BY entity_id, event_date ASC
        """,
        (*symbols, today, limit_per_symbol),
    ).fetchall()
    grouped = {symbol: [] for symbol in symbols}
    for row in rows:
        payload = load_json(row["payload_json"], {})
        grouped.setdefault(row["entity_id"], []).append(
            {
                "event_date": row["event_date"],
                "importance": row["importance"],
                "event_family": row["event_family"],
                "event_type": row["event_type"],
                "entity_id": row["entity_id"],
                "title": row["title"],
                "source_rel_path": row["source_rel_path"],
                "publish_time": row["publish_time"] or row["created_at"],
                "calendar_kind": payload.get("calendar_kind"),
                "summary": payload.get("summary"),
                "event_time_text": payload.get("event_time_text"),
                "record_date": payload.get("record_date"),
            }
        )
    return grouped


def latest_margin_focus_hits(conn: sqlite3.Connection, limit: int = 12) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        WITH active_pool AS (
            SELECT ts_code, GROUP_CONCAT(pool_type) AS pool_types
            FROM stock_pool_current
            GROUP BY ts_code
        ),
        ranked AS (
            SELECT
                m.trade_date,
                m.exchange,
                m.ts_code,
                COALESCE(m.security_name, m.ts_code) AS security_name,
                m.financing_balance,
                m.financing_buy_amount,
                m.margin_total_balance,
                m.securities_lending_balance_volume,
                active_pool.pool_types,
                ROW_NUMBER() OVER (
                    PARTITION BY m.ts_code
                    ORDER BY m.trade_date DESC, m.updated_at DESC
                ) AS rn
            FROM margin_security_detail m
            JOIN active_pool ON active_pool.ts_code = m.ts_code
        )
        SELECT
            trade_date,
            exchange,
            ts_code,
            security_name,
            financing_balance,
            financing_buy_amount,
            margin_total_balance,
            securities_lending_balance_volume,
            pool_types
        FROM ranked
        WHERE rn=1
        ORDER BY COALESCE(financing_balance, 0) DESC, ts_code
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [
        {
            "trade_date": row["trade_date"],
            "exchange": row["exchange"],
            "ts_code": row["ts_code"],
            "security_name": row["security_name"],
            "financing_balance": row["financing_balance"],
            "financing_buy_amount": row["financing_buy_amount"],
            "margin_total_balance": row["margin_total_balance"],
            "securities_lending_balance_volume": row["securities_lending_balance_volume"],
            "pool_types": row["pool_types"],
        }
        for row in rows
    ]


def latest_margin_hits_by_symbol(conn: sqlite3.Connection, symbols: list[str]) -> dict[str, dict[str, Any]]:
    if not symbols:
        return {}
    placeholders = ",".join("?" for _ in symbols)
    rows = conn.execute(
        f"""
        WITH active_pool AS (
            SELECT ts_code, GROUP_CONCAT(pool_type) AS pool_types
            FROM stock_pool_current
            GROUP BY ts_code
        ),
        ranked AS (
            SELECT
                m.trade_date,
                m.exchange,
                m.ts_code,
                COALESCE(m.security_name, m.ts_code) AS security_name,
                m.financing_balance,
                m.financing_buy_amount,
                m.margin_total_balance,
                m.securities_lending_balance_volume,
                active_pool.pool_types,
                ROW_NUMBER() OVER (
                    PARTITION BY m.ts_code
                    ORDER BY m.trade_date DESC, m.updated_at DESC
                ) AS rn
            FROM margin_security_detail m
            LEFT JOIN active_pool ON active_pool.ts_code = m.ts_code
            WHERE m.ts_code IN ({placeholders})
        )
        SELECT
            trade_date,
            exchange,
            ts_code,
            security_name,
            financing_balance,
            financing_buy_amount,
            margin_total_balance,
            securities_lending_balance_volume,
            pool_types
        FROM ranked
        WHERE rn=1
        ORDER BY ts_code
        """,
        symbols,
    ).fetchall()
    return {
        row["ts_code"]: {
            "trade_date": row["trade_date"],
            "exchange": row["exchange"],
            "ts_code": row["ts_code"],
            "security_name": row["security_name"],
            "financing_balance": row["financing_balance"],
            "financing_buy_amount": row["financing_buy_amount"],
            "margin_total_balance": row["margin_total_balance"],
            "securities_lending_balance_volume": row["securities_lending_balance_volume"],
            "pool_types": row["pool_types"],
        }
        for row in rows
    }


def latest_stock_connect_focus_hits(conn: sqlite3.Connection, limit: int = 12) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        WITH active_pool AS (
            SELECT ts_code, GROUP_CONCAT(pool_type) AS pool_types
            FROM stock_pool_current
            GROUP BY ts_code
        ),
        ranked AS (
            SELECT
                h.trade_date,
                h.route_key,
                h.route_name,
                h.direction,
                h.frequency,
                h.ts_code,
                COALESCE(h.security_name, h.ts_code) AS security_name,
                h.holding_quantity,
                active_pool.pool_types,
                ROW_NUMBER() OVER (
                    PARTITION BY h.ts_code, h.route_key
                    ORDER BY h.trade_date DESC, h.updated_at DESC
                ) AS rn
            FROM stock_connect_security_holding h
            JOIN active_pool ON active_pool.ts_code = h.ts_code
        )
        SELECT
            trade_date,
            route_key,
            route_name,
            direction,
            frequency,
            ts_code,
            security_name,
            holding_quantity,
            pool_types
        FROM ranked
        WHERE rn=1
        ORDER BY COALESCE(holding_quantity, 0) DESC, ts_code
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    return [
        {
            "trade_date": row["trade_date"],
            "route_key": row["route_key"],
            "route_name": row["route_name"],
            "direction": row["direction"],
            "frequency": row["frequency"],
            "ts_code": row["ts_code"],
            "security_name": row["security_name"],
            "holding_quantity": row["holding_quantity"],
            "pool_types": row["pool_types"],
        }
        for row in rows
    ]


def latest_stock_connect_hits_by_symbol(conn: sqlite3.Connection, symbols: list[str]) -> dict[str, list[dict[str, Any]]]:
    if not symbols:
        return {}
    placeholders = ",".join("?" for _ in symbols)
    rows = conn.execute(
        f"""
        WITH active_pool AS (
            SELECT ts_code, GROUP_CONCAT(pool_type) AS pool_types
            FROM stock_pool_current
            GROUP BY ts_code
        ),
        ranked AS (
            SELECT
                h.trade_date,
                h.route_key,
                h.route_name,
                h.direction,
                h.frequency,
                h.ts_code,
                COALESCE(h.security_name, h.ts_code) AS security_name,
                h.holding_quantity,
                active_pool.pool_types,
                ROW_NUMBER() OVER (
                    PARTITION BY h.ts_code, h.route_key
                    ORDER BY h.trade_date DESC, h.updated_at DESC
                ) AS rn
            FROM stock_connect_security_holding h
            LEFT JOIN active_pool ON active_pool.ts_code = h.ts_code
            WHERE h.ts_code IN ({placeholders})
        )
        SELECT
            trade_date,
            route_key,
            route_name,
            direction,
            frequency,
            ts_code,
            security_name,
            holding_quantity,
            pool_types
        FROM ranked
        WHERE rn=1
        ORDER BY ts_code, COALESCE(holding_quantity, 0) DESC, route_key
        """,
        symbols,
    ).fetchall()
    grouped = {symbol: [] for symbol in symbols}
    for row in rows:
        grouped.setdefault(row["ts_code"], []).append(
            {
                "trade_date": row["trade_date"],
                "route_key": row["route_key"],
                "route_name": row["route_name"],
                "direction": row["direction"],
                "frequency": row["frequency"],
                "ts_code": row["ts_code"],
                "security_name": row["security_name"],
                "holding_quantity": row["holding_quantity"],
                "pool_types": row["pool_types"],
            }
        )
    return grouped


def latest_stock_connect_market_summaries(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        WITH ranked AS (
            SELECT
                trade_date,
                route_key,
                route_name,
                direction,
                exchange,
                currency,
                buy_amount,
                sell_amount,
                total_amount,
                quota_status,
                payload_json,
                ROW_NUMBER() OVER (
                    PARTITION BY route_key
                    ORDER BY datetime(trade_date) DESC, updated_at DESC
                ) AS rn
            FROM stock_connect_market_summary
        )
        SELECT
            trade_date,
            route_key,
            route_name,
            direction,
            exchange,
            currency,
            buy_amount,
            sell_amount,
            total_amount,
            quota_status,
            payload_json
        FROM ranked
        WHERE rn = 1
        ORDER BY route_key
        """
    ).fetchall()
    items = []
    for row in rows:
        payload = load_json(row["payload_json"], {})
        realtime_probe = payload.get("realtime_probe") or {}
        items.append(
            {
                "trade_date": row["trade_date"],
                "route_key": row["route_key"],
                "route_name": row["route_name"],
                "direction": row["direction"],
                "exchange": row["exchange"],
                "currency": row["currency"],
                "buy_amount": row["buy_amount"],
                "sell_amount": row["sell_amount"],
                "total_amount": row["total_amount"],
                "quota_status": row["quota_status"],
                "buy_sell_estimated": bool(payload.get("buy_sell_estimated")),
                "buy_sell_display_basis": payload.get("buy_sell_display_basis"),
                "estimate_source": payload.get("estimate_source"),
                "estimate_unavailable_reason": payload.get("estimate_unavailable_reason"),
                "realtime_probe_trade_date": realtime_probe.get("trade_date"),
                "realtime_probe_status_label": realtime_probe.get("status_label"),
                "realtime_probe_buy_sell_amount": realtime_probe.get("buy_sell_amount"),
                "realtime_probe_net_buy_amount": realtime_probe.get("net_buy_amount"),
            }
        )
    return items


def registry_timeline(conn: sqlite3.Connection, limit: int = 24) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT entity_type, entity_id, status, created_at
        FROM task_registry_entity_latest
        ORDER BY datetime(created_at) DESC, id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    items = []
    for row in rows:
        items.append(
            {
                "entity_type": row["entity_type"],
                "entity_id": row["entity_id"],
                "status": row["status"],
                "created_at": row["created_at"],
            }
        )
    return items


def today_registry_counts(conn: sqlite3.Connection, now: datetime) -> list[dict[str, Any]]:
    start_of_day = now.strftime("%Y-%m-%d 00:00:00")
    rows = conn.execute(
        """
        SELECT entity_type, COUNT(*) AS count
        FROM task_registry_entity_latest
        WHERE created_at >= ?
        GROUP BY entity_type
        ORDER BY count DESC, entity_type
        """,
        (start_of_day,),
    ).fetchall()
    return [{"entity_type": row["entity_type"], "count": row["count"]} for row in rows]


def simplify_priority(priority: dict[str, Any] | None) -> str | None:
    if not priority:
        return None
    return priority.get("label")


def simplify_public_signal_item(item: dict[str, Any] | None) -> dict[str, Any]:
    item = item or {}
    return {
        "ts_code": item.get("ts_code"),
        "name": item.get("name"),
        "provider": item.get("provider"),
        "published_at": item.get("published_at"),
        "snapshot_date": item.get("snapshot_date"),
        "freshness_label": item.get("freshness_label"),
        "stance_label": item.get("stance_label"),
        "stance_summary": item.get("stance_summary"),
        "summary": item.get("summary"),
        "mean_consensus": item.get("mean_consensus"),
        "analysts_count": item.get("analysts_count"),
        "last_close_raw": item.get("last_close_raw"),
        "average_target_raw": item.get("average_target_raw"),
        "spread_avg_target_pct": item.get("spread_avg_target_pct"),
        "source_rel_path": item.get("source_rel_path"),
    }


def simplify_external_research_item(item: dict[str, Any] | None) -> dict[str, Any]:
    item = item or {}
    return {
        "ts_code": item.get("ts_code"),
        "name": item.get("name"),
        "sector": item.get("sector"),
        "pool_types": item.get("pool_types") or [],
        "source_kind": item.get("source_kind"),
        "title": item.get("title"),
        "published_at": item.get("published_at"),
        "org_name": item.get("org_name"),
        "rating_name": item.get("rating_name"),
        "target_price_yuan": item.get("target_price_yuan"),
        "source_rel_path": item.get("source_rel_path"),
    }


def simplify_official_material_item(item: dict[str, Any] | None) -> dict[str, Any]:
    item = item or {}
    return {
        "ts_code": item.get("ts_code"),
        "name": item.get("name"),
        "sector": item.get("sector"),
        "pool_types": item.get("pool_types") or [],
        "freshness_label": item.get("freshness_label"),
        "item_count": item.get("item_count"),
        "summary": item.get("summary"),
        "latest_title": item.get("latest_title"),
        "latest_publish_time": item.get("latest_publish_time"),
        "latest_event_type": item.get("latest_event_type"),
        "latest_source_key": item.get("latest_source_key"),
        "latest_summary": item.get("latest_summary"),
        "source_rel_paths": item.get("source_rel_paths") or [],
        "items": item.get("items") or [],
    }


def simplify_public_transcript_item(item: dict[str, Any] | None) -> dict[str, Any]:
    item = item or {}
    return {
        "ts_code": item.get("ts_code"),
        "name": item.get("name"),
        "sector": item.get("sector"),
        "pool_types": item.get("pool_types") or [],
        "provider": item.get("provider"),
        "freshness_label": item.get("freshness_label"),
        "published_at": item.get("published_at"),
        "quarter_label": item.get("quarter_label"),
        "speaker_count": item.get("speaker_count"),
        "speakers": item.get("speakers") or [],
        "summary": item.get("summary"),
        "source_rel_path": item.get("source_rel_path"),
    }


def simplify_watch_item(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "ts_code": item.get("ts_code"),
        "name": item.get("name"),
        "sector": item.get("sector"),
        "card_rel_path": item.get("card_rel_path"),
        "primary_pool": item.get("primary_pool") or ((item.get("pool_types") or [None])[0]),
        "objective_view": item.get("objective_view"),
        "priority": simplify_priority(item.get("priority")),
        "priority_score": (item.get("priority") or {}).get("score"),
        "latest_pct_chg": item.get("latest_pct_chg"),
        "latest_close": item.get("latest_close"),
        "latest_trade_date": item.get("latest_trade_date"),
        "trend_strength": item.get("trend_strength"),
        "rsi_14": item.get("rsi_14"),
        "ma_20": item.get("ma_20"),
        "ma_60": item.get("ma_60"),
        "ma_120": item.get("ma_120"),
        "pe_ttm": item.get("pe_ttm"),
        "pb": item.get("pb"),
        "revenue_yoy": item.get("revenue_yoy"),
        "net_profit_yoy": item.get("net_profit_yoy"),
        "signal_tags": item.get("signal_tags") or [],
        "trend_label": (item.get("trend_state") or {}).get("label"),
        "trend_summary": (item.get("trend_state") or {}).get("summary"),
        "valuation_label": (item.get("valuation_pressure") or {}).get("label"),
        "valuation_summary": (item.get("valuation_pressure") or {}).get("summary"),
        "research_label": (item.get("research_staleness") or {}).get("label"),
        "research_summary": (item.get("research_staleness") or {}).get("summary"),
        "quality_score": item.get("quality_score"),
        "rotation_in_score": item.get("rotation_in_score"),
        "rotation_out_score": item.get("rotation_out_score"),
        "watchpoints": item.get("watchpoints") or [],
        "next_check_items": item.get("next_check_items") or [],
        "capital_flow_summary": item.get("capital_flow_summary"),
        "event_summary": item.get("event_summary"),
        "auxiliary_watchpoints": item.get("auxiliary_watchpoints") or [],
        "capital_flow_signal_score": item.get("capital_flow_signal_score"),
        "event_signal_score": item.get("event_signal_score"),
        "margin_balance": item.get("margin_balance") or {},
        "stock_connect": item.get("stock_connect") or {},
        "stock_connect_hits": item.get("stock_connect_hits") or [],
        "recent_events": item.get("recent_events") or [],
        "event_calendar": item.get("event_calendar") or [],
        "upcoming_event_calendar": item.get("upcoming_event_calendar") or [],
        "external_research_org": ((item.get("external_research") or {}).get("org_name")),
        "external_research_published_at": ((item.get("external_research") or {}).get("published_at")),
        "external_research_rating": ((item.get("external_research") or {}).get("rating_name")),
        "external_research_kind": ((item.get("external_research") or {}).get("source_kind")),
        "source_rel_path": ((item.get("external_research") or {}).get("source_rel_path")),
        "official_material_freshness": ((item.get("official_material") or {}).get("freshness_label")),
        "official_material_item_count": ((item.get("official_material") or {}).get("item_count")),
        "official_material_summary": ((item.get("official_material") or {}).get("summary")),
        "official_material_latest_title": ((item.get("official_material") or {}).get("latest_title")),
        "official_material_latest_publish_time": ((item.get("official_material") or {}).get("latest_publish_time")),
        "official_material_latest_event_type": ((item.get("official_material") or {}).get("latest_event_type")),
        "official_material_latest_source_key": ((item.get("official_material") or {}).get("latest_source_key")),
        "official_material_source_rel_paths": ((item.get("official_material") or {}).get("source_rel_paths")) or [],
        "public_transcript_provider": ((item.get("public_transcript") or {}).get("provider")),
        "public_transcript_published_at": ((item.get("public_transcript") or {}).get("published_at")),
        "public_transcript_freshness": ((item.get("public_transcript") or {}).get("freshness_label")),
        "public_transcript_quarter_label": ((item.get("public_transcript") or {}).get("quarter_label")),
        "public_transcript_speaker_count": ((item.get("public_transcript") or {}).get("speaker_count")),
        "public_transcript_summary": ((item.get("public_transcript") or {}).get("summary")),
        "public_transcript_source_rel_path": ((item.get("public_transcript") or {}).get("source_rel_path")),
        "public_analyst_provider": ((item.get("public_analyst_signal") or {}).get("provider")),
        "public_analyst_published_at": ((item.get("public_analyst_signal") or {}).get("published_at")),
        "public_analyst_freshness": ((item.get("public_analyst_signal") or {}).get("freshness_label")),
        "public_analyst_label": ((item.get("public_analyst_signal") or {}).get("stance_label")),
        "public_analyst_summary": ((item.get("public_analyst_signal") or {}).get("summary")),
        "public_analyst_stance_summary": ((item.get("public_analyst_signal") or {}).get("stance_summary")),
        "public_analyst_mean_consensus": ((item.get("public_analyst_signal") or {}).get("mean_consensus")),
        "public_analyst_analysts_count": ((item.get("public_analyst_signal") or {}).get("analysts_count")),
        "public_analyst_average_target_raw": ((item.get("public_analyst_signal") or {}).get("average_target_raw")),
        "public_analyst_last_close_raw": ((item.get("public_analyst_signal") or {}).get("last_close_raw")),
        "public_analyst_spread_avg_target_pct": ((item.get("public_analyst_signal") or {}).get("spread_avg_target_pct")),
        "public_analyst_source_rel_path": ((item.get("public_analyst_signal") or {}).get("source_rel_path")),
    }


def simplify_deep_candidate_item(item: dict[str, Any] | None) -> dict[str, Any]:
    item = item or {}
    return {
        "ts_code": item.get("ts_code"),
        "name": item.get("name"),
        "market": item.get("market"),
        "sector": item.get("sector"),
        "pool_types": item.get("pool_types") or [],
        "primary_pool": item.get("primary_pool"),
        "theme_ids": item.get("theme_ids") or [],
        "theme_labels": item.get("theme_labels") or [],
        "role": item.get("role"),
        "latest_trade_date": item.get("latest_trade_date"),
        "latest_close": item.get("latest_close"),
        "latest_pct_chg": item.get("latest_pct_chg"),
        "ma_20": item.get("ma_20"),
        "ma_60": item.get("ma_60"),
        "ma_120": item.get("ma_120"),
        "return_20d": item.get("return_20d"),
        "return_60d": item.get("return_60d"),
        "trend_label": item.get("trend_label"),
        "trend_summary": item.get("trend_summary"),
        "rsi_14": item.get("rsi_14"),
        "pe_ttm": item.get("pe_ttm"),
        "pb": item.get("pb"),
        "revenue_yoy": item.get("revenue_yoy"),
        "net_profit_yoy": item.get("net_profit_yoy"),
        "target_gap_pct": item.get("target_gap_pct"),
        "analyst_gap_pct": item.get("analyst_gap_pct"),
        "event_count_21d": item.get("event_count_21d"),
        "source_count": item.get("source_count"),
        "undervaluation_score": item.get("undervaluation_score"),
        "bucket": item.get("bucket"),
        "bucket_label": item.get("bucket_label"),
        "summary": item.get("summary"),
        "why": item.get("why") or [],
        "risks": item.get("risks") or [],
        "source_rel_paths": item.get("source_rel_paths") or [],
    }


def simplify_market_flow_item(item: dict[str, Any] | None) -> dict[str, Any]:
    item = item or {}
    return {
        "market": item.get("market"),
        "market_label": item.get("market_label"),
        "symbol": item.get("symbol") or item.get("ts_code"),
        "ts_code": item.get("ts_code") or item.get("symbol"),
        "name": item.get("name"),
        "trade_date": item.get("trade_date"),
        "close": item.get("close"),
        "pct_chg": item.get("pct_chg"),
        "vol": item.get("vol"),
        "amount": item.get("amount"),
        "pool_types": item.get("pool_types") or [],
        "volume_ratio_20d": item.get("volume_ratio_20d"),
        "amount_ratio_20d": item.get("amount_ratio_20d"),
        "flow_signal_score": item.get("flow_signal_score"),
        "reason_summary": item.get("reason_summary"),
        "news_summary": item.get("news_summary"),
        "latest_event_title": item.get("latest_event_title"),
        "latest_event_time": item.get("latest_event_time"),
        "latest_event_family": item.get("latest_event_family"),
        "latest_event_type": item.get("latest_event_type"),
        "latest_event_rel_path": item.get("latest_event_rel_path"),
        "latest_event_age_days": item.get("latest_event_age_days"),
        "latest_event_importance": item.get("latest_event_importance"),
    }


def simplify_forecast_item(item: dict[str, Any] | None) -> dict[str, Any]:
    item = item or {}
    return {
        "proxy_id": item.get("proxy_id"),
        "proxy_type": item.get("proxy_type"),
        "ts_code": item.get("ts_code"),
        "symbol": item.get("symbol") or item.get("ts_code"),
        "name": item.get("name"),
        "market": item.get("market"),
        "market_label": item.get("market_label"),
        "sector": item.get("sector"),
        "pool_types": item.get("pool_types") or [],
        "primary_pool": item.get("primary_pool"),
        "description": item.get("description"),
        "member_count": item.get("member_count"),
        "used_member_count": item.get("used_member_count"),
        "latest_trade_date": item.get("latest_trade_date"),
        "latest_close": item.get("latest_close"),
        "latest_pct_chg": item.get("latest_pct_chg"),
        "realized_volatility_20d": item.get("realized_volatility_20d"),
        "bias_label": item.get("bias_label"),
        "confidence": item.get("confidence"),
        "confidence_label": item.get("confidence_label"),
        "next_day": item.get("next_day") or {},
        "five_day": item.get("five_day") or {},
        "ma_20": item.get("ma_20"),
        "ma_60": item.get("ma_60"),
        "ma_120": item.get("ma_120"),
        "trend_strength": item.get("trend_strength"),
        "rsi_14": item.get("rsi_14"),
        "driver_lines": item.get("driver_lines") or [],
        "event_summary": item.get("event_summary"),
        "event_published_at": item.get("event_published_at"),
        "event_type": item.get("event_type"),
        "event_source_rel_path": item.get("event_source_rel_path"),
        "summary_line": item.get("summary_line"),
    }


def simplify_rotation_pair(pair: dict[str, Any]) -> dict[str, Any]:
    add_item = pair.get("add") or {}
    remove_item = pair.get("remove") or {}
    return {
        "fit_label": pair.get("fit_label"),
        "pair_score": pair.get("pair_score"),
        "expected_positive_change": (pair.get("expected_positive_change") or [])[:3],
        "risk_flags": (pair.get("risk_flags") or [])[:3],
        "add": {
            "ts_code": add_item.get("ts_code"),
            "name": add_item.get("name"),
            "primary_pool": add_item.get("primary_pool"),
            "objective_view": add_item.get("objective_view"),
            "latest_pct_chg": add_item.get("latest_pct_chg"),
            "public_transcript_freshness": ((add_item.get("public_transcript") or {}).get("freshness_label")),
            "public_transcript_summary": ((add_item.get("public_transcript") or {}).get("summary")),
        },
        "remove": {
            "ts_code": remove_item.get("ts_code"),
            "name": remove_item.get("name"),
            "primary_pool": remove_item.get("primary_pool"),
            "objective_view": remove_item.get("objective_view"),
            "latest_pct_chg": remove_item.get("latest_pct_chg"),
            "public_transcript_freshness": ((remove_item.get("public_transcript") or {}).get("freshness_label")),
            "public_transcript_summary": ((remove_item.get("public_transcript") or {}).get("summary")),
        },
    }


def simplify_action(action: dict[str, Any]) -> dict[str, Any]:
    return {
        "action_id": action.get("action_id"),
        "title": action.get("title"),
        "action_type": action.get("action_type"),
        "priority": action.get("priority"),
        "summary": action.get("summary"),
        "gate_status": action.get("gate_status"),
        "trade_amount": action.get("trade_amount"),
        "trade_amount_pct": action.get("trade_amount_pct"),
        "subject": action.get("subject"),
        "add": action.get("add"),
        "remove": action.get("remove"),
        "rationale": action.get("rationale") or [],
        "risk_flags": action.get("risk_flags") or [],
        "next_checks": action.get("next_checks") or [],
        "source_refs": action.get("source_refs") or [],
    }


def parse_ymd(value: str | None) -> date | None:
    if value in (None, ""):
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def date_lag_days(value: str | None, today: date) -> int | None:
    parsed = parse_ymd(value)
    if parsed is None:
        return None
    return (today - parsed).days


def run_log_summary(now: datetime, limit: int = 20) -> dict[str, Any]:
    recent = deque(maxlen=limit)
    today_counts: Counter[str] = Counter()
    today_script_counts: Counter[str] = Counter()
    last_freshness_warning = None

    if not RUN_LOG_PATH.exists():
        return {
            "path": str(RUN_LOG_PATH),
            "exists": False,
            "today_status_counts": {},
            "today_script_count": 0,
            "recent_entries": [],
            "freshness_warning": None,
        }

    today_prefix = now.strftime("%Y-%m-%d")
    with RUN_LOG_PATH.open("r", encoding="utf-8") as handle:
        for raw_line in handle:
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                item = json.loads(raw_line)
            except json.JSONDecodeError:
                continue

            recent.append(item)
            time_text = item.get("time") or ""
            if time_text.startswith(today_prefix):
                today_counts[item.get("status") or "unknown"] += 1
                script_name = item.get("script") or "unknown"
                today_script_counts[script_name] += 1

            if item.get("script") == "check_data_freshness.py":
                metrics = item.get("metrics") or {}
                stale_or_missing = metrics.get("stale_or_missing") or []
                if stale_or_missing:
                    last_freshness_warning = {
                        "time": item.get("time"),
                        "status": item.get("status"),
                        "mode": metrics.get("mode"),
                        "expected_cn_date": metrics.get("expected_cn_date"),
                        "expected_hk_date": metrics.get("expected_hk_date"),
                        "expected_cn_factor_date": metrics.get("expected_cn_factor_date"),
                        "expected_us_date": metrics.get("expected_us_date"),
                        "stale_or_missing": stale_or_missing,
                        "checks": metrics.get("checks") or [],
                    }
                else:
                    last_freshness_warning = None

    entries = []
    for item in reversed(recent):
        metrics = item.get("metrics") or {}
        entries.append(
            {
                "time": item.get("time"),
                "script": item.get("script"),
                "status": item.get("status"),
                "message": item.get("message"),
                "summary_rel_path": metrics.get("summary_rel_path"),
                "entity_id": metrics.get("entity_id"),
            }
        )

    return {
        "path": str(RUN_LOG_PATH),
        "exists": True,
        "today_status_counts": dict(today_counts),
        "today_script_count": len(today_script_counts),
        "recent_entries": entries,
        "freshness_warning": last_freshness_warning,
    }


def scheduler_run_summary(now: datetime, limit: int = 12) -> dict[str, Any]:
    if not SCHEDULER_RUN_ROOT.exists():
        return {
            "path": str(SCHEDULER_RUN_ROOT),
            "exists": False,
            "today_status_counts": {},
            "today_run_count": 0,
            "recent_runs": [],
            "latest_run": None,
            "latest_by_job": {},
        }

    today_prefix = now.strftime("%Y%m%d")
    recent_runs: list[dict[str, Any]] = []
    latest_by_job: dict[str, dict[str, Any]] = {}
    today_status_counts: Counter[str] = Counter()
    today_run_count = 0

    def sort_key(path: Path) -> str:
        return path.name

    for run_dir in sorted((path for path in SCHEDULER_RUN_ROOT.iterdir() if path.is_dir()), key=sort_key, reverse=True):
        summary_path = run_dir / "summary.json"
        if not summary_path.exists():
            continue
        try:
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue

        stem = run_dir.name
        if "__" in stem:
            run_stamp, fallback_job_id = stem.split("__", 1)
        else:
            run_stamp, fallback_job_id = stem, "unknown"
        job_id = summary.get("job_id") or fallback_job_id
        item = {
            "run_id": stem,
            "job_id": job_id,
            "label": summary.get("label") or job_id,
            "status": summary.get("status") or "unknown",
            "started_at": summary.get("started_at"),
            "finished_at": summary.get("finished_at"),
            "failed_count": summary.get("failed_count"),
            "command_count": summary.get("command_count"),
            "summary_rel_path": relative_to_project(summary_path),
            "run_dir_rel_path": relative_to_project(run_dir),
        }
        if len(recent_runs) < limit:
            recent_runs.append(item)
        latest_by_job.setdefault(job_id, item)
        if run_stamp.startswith(today_prefix):
            today_run_count += 1
            today_status_counts[item["status"]] += 1

    return {
        "path": str(SCHEDULER_RUN_ROOT),
        "exists": True,
        "today_status_counts": dict(today_status_counts),
        "today_run_count": today_run_count,
        "recent_runs": recent_runs,
        "latest_run": recent_runs[0] if recent_runs else None,
        "latest_by_job": latest_by_job,
    }


def build_state_version(state: dict[str, Any]) -> str:
    operations = state.get("operations") or {}
    scheduler = operations.get("scheduler") or {}
    run_log = operations.get("run_log") or {}
    overview = state.get("overview") or {}
    deep_analysis = state.get("deep_analysis") or {}
    opportunity_engine = state.get("opportunity_engine") or {}
    analysis_forecast = state.get("analysis_forecast") or {}
    reporting = state.get("reporting") or {}
    portfolio_action = state.get("portfolio_action") or {}
    risk = state.get("risk") or {}
    events = state.get("events") or {}
    source_registry = state.get("source_registry") or {}
    version_basis = {
        "a_share_trade_date": overview.get("a_share_trade_date"),
        "hk_trade_date": overview.get("hk_trade_date"),
        "us_trade_date": overview.get("us_trade_date"),
        "a_share_expected_trade_date": overview.get("a_share_expected_trade_date"),
        "hk_expected_trade_date": overview.get("hk_expected_trade_date"),
        "us_expected_trade_date": overview.get("us_expected_trade_date"),
        "latest_daily_report_date": overview.get("latest_daily_report_date"),
        "today_script_status_counts": overview.get("today_script_status_counts"),
        "today_script_count": overview.get("today_script_count"),
        "deep_analysis_created_at": deep_analysis.get("created_at"),
        "opportunity_radar_created_at": ((opportunity_engine.get("radar") or {}).get("created_at")),
        "opportunity_lifecycle_created_at": ((opportunity_engine.get("lifecycle") or {}).get("created_at")),
        "paper_watchlist_created_at": ((opportunity_engine.get("paper_watchlist") or {}).get("created_at")),
        "paper_performance_created_at": ((opportunity_engine.get("paper_performance") or {}).get("created_at")),
        "analysis_forecast_created_at": analysis_forecast.get("created_at"),
        "latest_report_updated_at": reporting.get("latest_report_updated_at"),
        "report_surface_date": reporting.get("report_surface_date"),
        "latest_report_is_aligned": reporting.get("latest_report_is_aligned"),
        "dispatch_board_updated_at": reporting.get("dispatch_board_updated_at"),
        "action_created_at": portfolio_action.get("created_at"),
        "risk_created_at": risk.get("created_at"),
        "risk_decision_created_at": ((risk.get("decision") or {}).get("created_at")),
        "event_calendar_created_at": ((events.get("event_calendar_snapshot") or {}).get("created_at")),
        "source_registry_created_at": source_registry.get("created_at"),
        "scheduler_latest_run": scheduler.get("latest_run"),
        "run_log_latest_entry": ((run_log.get("recent_entries") or [None])[0]),
        "freshness_warning": run_log.get("freshness_warning"),
    }
    payload = json.dumps(version_basis, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:16]


def build_dashboard_state(now: datetime | None = None, registry_limit: int = 24, run_log_limit: int = 20) -> dict[str, Any]:
    now = now or datetime.now()
    today = now.date()

    conn = connect_db()
    try:
        snapshots = {entity_type: latest_snapshot(conn, entity_type) for entity_type in KEY_ENTITY_TYPES}
        trades = latest_trade_dates(conn)
        pools = pool_counts(conn)
        positions = open_position_summary(conn)
        risks = risk_summary(conn)
        registry_counts = today_registry_counts(conn, now)
        timeline = registry_timeline(conn, limit=registry_limit)
        market_events = recent_market_events(conn)
        market_events_by_family = recent_market_events_by_family(conn)
        upcoming_events = upcoming_market_events(conn)
        margin_focus_hits = latest_margin_focus_hits(conn)
        stock_connect_focus_hits = latest_stock_connect_focus_hits(conn)
        stock_connect_market_summaries = latest_stock_connect_market_summaries(conn)
        detail_symbols: set[str] = set()
        strategy_snapshot = snapshots.get("strategy_watch_batch") or {}
        strategy_snapshot_payload = strategy_snapshot.get("payload") or {}
        for item in strategy_snapshot_payload.get("top_focus_items") or []:
            ts_code = item.get("ts_code")
            if ts_code:
                detail_symbols.add(ts_code)

        rotation_snapshot = snapshots.get("rotation_candidate_snapshot") or {}
        rotation_snapshot_payload = rotation_snapshot.get("payload") or {}
        for bucket_name in ("top_add_candidates", "top_reduce_candidates"):
            for item in rotation_snapshot_payload.get(bucket_name) or []:
                ts_code = item.get("ts_code")
                if ts_code:
                    detail_symbols.add(ts_code)

        action_snapshot = snapshots.get("portfolio_action_memo_snapshot") or {}
        action_snapshot_payload = action_snapshot.get("payload") or {}
        for action in action_snapshot_payload.get("actions") or []:
            for leg_name in ("add", "remove", "subject"):
                ts_code = ((action.get(leg_name) or {}).get("ts_code"))
                if ts_code:
                    detail_symbols.add(ts_code)

        deep_analysis_snapshot = snapshots.get("deep_market_analysis_snapshot") or {}
        deep_analysis_payload = deep_analysis_snapshot.get("payload") or {}
        for bucket_name in ("a_share_candidates", "us_candidates"):
            for item in deep_analysis_payload.get(bucket_name) or []:
                ts_code = item.get("ts_code")
                if ts_code:
                    detail_symbols.add(ts_code)

        opportunity_radar_snapshot = snapshots.get("opportunity_radar_snapshot") or {}
        opportunity_radar_payload = opportunity_radar_snapshot.get("payload") or {}
        for market_items in (opportunity_radar_payload.get("markets") or {}).values():
            for item in market_items or []:
                ts_code = item.get("ts_code")
                if ts_code:
                    detail_symbols.add(ts_code)
        paper_watchlist_snapshot = snapshots.get("paper_trade_watchlist_snapshot") or {}
        paper_watchlist_payload = paper_watchlist_snapshot.get("payload") or {}
        for item in paper_watchlist_payload.get("tickets") or []:
            ts_code = item.get("ts_code")
            if ts_code:
                detail_symbols.add(ts_code)
        lifecycle_snapshot = snapshots.get("opportunity_lifecycle_snapshot") or {}
        lifecycle_payload = lifecycle_snapshot.get("payload") or {}
        for item in lifecycle_payload.get("items") or []:
            ts_code = item.get("ts_code")
            if ts_code:
                detail_symbols.add(ts_code)
        paper_performance_snapshot = snapshots.get("paper_watch_performance_snapshot") or {}
        paper_performance_payload = paper_performance_snapshot.get("payload") or {}
        for item in paper_performance_payload.get("items") or []:
            ts_code = item.get("ts_code")
            if ts_code:
                detail_symbols.add(ts_code)

        forecast_snapshot = snapshots.get("price_range_forecast_snapshot") or {}
        forecast_payload = forecast_snapshot.get("payload") or {}
        for item in forecast_payload.get("equities") or []:
            ts_code = item.get("ts_code")
            if ts_code:
                detail_symbols.add(ts_code)

        for position in positions["positions"]:
            ts_code = position.get("ts_code")
            if ts_code:
                detail_symbols.add(ts_code)

        detail_symbol_list = sorted(detail_symbols)
        detail_market_events = recent_market_events_for_symbols(conn, detail_symbol_list)
        detail_upcoming_events = upcoming_market_events_for_symbols(conn, detail_symbol_list)
        detail_margin_hits = latest_margin_hits_by_symbol(conn, detail_symbol_list)
        detail_stock_connect_hits = latest_stock_connect_hits_by_symbol(conn, detail_symbol_list)
        detail_risk_alerts = recent_risk_alerts_for_symbols(conn, detail_symbol_list)
        detail_external_research = {
            ts_code: latest_external_research_snapshot(conn, ts_code)
            for ts_code in detail_symbol_list
        }
        detail_official_materials = {
            ts_code: summarize_official_materials(conn, ts_code, limit=4)
            for ts_code in detail_symbol_list
        }
        detail_public_transcripts = {
            ts_code: latest_public_transcript_snapshot(conn, ts_code)
            for ts_code in detail_symbol_list
        }
    finally:
        conn.close()

    run_log = run_log_summary(now, limit=run_log_limit)
    scheduler = scheduler_run_summary(now, limit=12)

    daily_reporting = snapshots["daily_reporting_snapshot"] or {}
    daily_candidate = snapshots["daily_report_candidate"] or {}
    deep_analysis_snapshot = snapshots["deep_market_analysis_snapshot"] or {}
    deep_analysis_payload = deep_analysis_snapshot.get("payload") or {}
    deep_analysis_relationships = deep_analysis_snapshot.get("relationships") or {}
    daily_payload = daily_reporting.get("payload") or {}
    daily_relationships = daily_reporting.get("relationships") or {}
    daily_candidate_payload = daily_candidate.get("payload") or {}
    daily_candidate_relationships = daily_candidate.get("relationships") or {}
    latest_report_date = daily_reporting.get("entity_id")

    dispatch_board_patch = {}
    if latest_report_date:
        patch_conn = connect_db()
        try:
            dispatch_board_patch = (
                latest_snapshot_for_entity(patch_conn, "dispatch_board_patch_candidate", latest_report_date) or {}
            )
        finally:
            patch_conn.close()

    strategy_watch = snapshots["strategy_watch_batch"] or {}
    strategy_payload = strategy_watch.get("payload") or {}
    strategy_relationships = strategy_watch.get("relationships") or {}

    rotation = snapshots["rotation_candidate_snapshot"] or {}
    rotation_payload = rotation.get("payload") or {}
    rotation_relationships = rotation.get("relationships") or {}

    execution = snapshots["rotation_execution_plan_snapshot"] or {}
    execution_payload = execution.get("payload") or {}
    execution_relationships = execution.get("relationships") or {}

    action_memo = snapshots["portfolio_action_memo_snapshot"] or {}
    action_payload = action_memo.get("payload") or {}
    action_relationships = action_memo.get("relationships") or {}

    precheck_snapshot = snapshots["execution_precheck_snapshot"] or {}
    precheck_payload = precheck_snapshot.get("payload") or {}
    precheck_relationships = precheck_snapshot.get("relationships") or {}

    risk_snapshot = snapshots["risk_monitor_snapshot"] or {}
    risk_payload = risk_snapshot.get("payload") or {}
    risk_decision_snapshot = snapshots["trade_risk_decision_snapshot"] or {}
    risk_decision_payload = risk_decision_snapshot.get("payload") or {}
    risk_decision_relationships = risk_decision_snapshot.get("relationships") or {}

    margin_snapshot = snapshots["margin_balance_snapshot"] or {}
    margin_payload = margin_snapshot.get("payload") or {}
    margin_relationships = margin_snapshot.get("relationships") or {}

    stock_connect_snapshot = snapshots["stock_connect_flow_snapshot"] or {}
    stock_connect_payload = stock_connect_snapshot.get("payload") or {}
    stock_connect_relationships = stock_connect_snapshot.get("relationships") or {}
    capital_flow_fact_sheet = build_capital_flow_fact_sheet_from_payloads(margin_payload, stock_connect_payload)

    event_calendar_snapshot = snapshots["event_calendar_snapshot"] or {}
    event_calendar_payload = event_calendar_snapshot.get("payload") or {}
    event_calendar_relationships = event_calendar_snapshot.get("relationships") or {}
    upcoming_event_calendar_snapshot = snapshots["upcoming_event_calendar_snapshot"] or {}
    upcoming_event_calendar_payload = upcoming_event_calendar_snapshot.get("payload") or {}
    upcoming_event_calendar_relationships = upcoming_event_calendar_snapshot.get("relationships") or {}

    market_event_snapshot = snapshots["market_event_snapshot"] or {}
    market_event_payload = market_event_snapshot.get("payload") or {}
    market_event_relationships = market_event_snapshot.get("relationships") or {}

    market_flow_snapshot = snapshots["market_flow_anomaly_snapshot"] or {}
    market_flow_payload = market_flow_snapshot.get("payload") or {}
    market_flow_relationships = market_flow_snapshot.get("relationships") or {}

    opportunity_radar_snapshot = snapshots["opportunity_radar_snapshot"] or {}
    opportunity_radar_payload = opportunity_radar_snapshot.get("payload") or {}
    opportunity_radar_relationships = opportunity_radar_snapshot.get("relationships") or {}
    opportunity_lifecycle_snapshot = snapshots["opportunity_lifecycle_snapshot"] or {}
    opportunity_lifecycle_payload = opportunity_lifecycle_snapshot.get("payload") or {}
    opportunity_lifecycle_relationships = opportunity_lifecycle_snapshot.get("relationships") or {}
    strategy_evidence_snapshot = snapshots["strategy_evidence_snapshot"] or {}
    strategy_evidence_payload = strategy_evidence_snapshot.get("payload") or {}
    strategy_evidence_relationships = strategy_evidence_snapshot.get("relationships") or {}
    attack_defense_snapshot = snapshots["thesis_attack_defense_snapshot"] or {}
    attack_defense_payload = attack_defense_snapshot.get("payload") or {}
    attack_defense_relationships = attack_defense_snapshot.get("relationships") or {}
    paper_watchlist_snapshot = snapshots["paper_trade_watchlist_snapshot"] or {}
    paper_watchlist_payload = paper_watchlist_snapshot.get("payload") or {}
    paper_watchlist_relationships = paper_watchlist_snapshot.get("relationships") or {}
    paper_performance_snapshot = snapshots["paper_watch_performance_snapshot"] or {}
    paper_performance_payload = paper_performance_snapshot.get("payload") or {}
    paper_performance_relationships = paper_performance_snapshot.get("relationships") or {}

    forecast_snapshot = snapshots["price_range_forecast_snapshot"] or {}
    forecast_payload = forecast_snapshot.get("payload") or {}
    forecast_relationships = forecast_snapshot.get("relationships") or {}

    source_registry_snapshot = snapshots["input_source_registry_snapshot"] or {}
    source_registry_payload = source_registry_snapshot.get("payload") or {}
    source_registry_relationships = source_registry_snapshot.get("relationships") or {}

    latest_report_rel_path = (
        daily_relationships.get("latest_report_rel_path") or daily_payload.get("latest_report_rel_path")
    )
    daily_candidate_rel_path = (
        daily_candidate_relationships.get("candidate_rel_path") or daily_candidate_payload.get("candidate_rel_path")
    )
    dispatch_board_rel_path = (
        daily_relationships.get("dispatch_board_rel_path") or daily_payload.get("dispatch_board_rel_path")
    )
    strategy_rel_path = strategy_relationships.get("summary_rel_path") or strategy_payload.get("summary_rel_path")
    rotation_rel_path = rotation_relationships.get("summary_rel_path") or rotation_payload.get("summary_rel_path")
    execution_rel_path = execution_relationships.get("summary_rel_path") or execution_payload.get("summary_rel_path")
    action_rel_path = action_relationships.get("summary_rel_path") or action_payload.get("summary_rel_path")
    precheck_rel_path = (
        precheck_relationships.get("summary_rel_path") or precheck_payload.get("summary_rel_path")
    )
    risk_decision_rel_path = (
        risk_decision_relationships.get("summary_rel_path") or risk_decision_payload.get("summary_rel_path")
    )
    margin_rel_path = margin_relationships.get("summary_rel_path") or margin_payload.get("summary_rel_path")
    stock_connect_rel_path = (
        stock_connect_relationships.get("summary_rel_path") or stock_connect_payload.get("summary_rel_path")
    )
    event_calendar_rel_path = (
        event_calendar_relationships.get("summary_rel_path") or event_calendar_payload.get("summary_rel_path")
    )
    upcoming_event_calendar_rel_path = (
        upcoming_event_calendar_relationships.get("summary_rel_path")
        or upcoming_event_calendar_payload.get("summary_rel_path")
    )
    market_event_rel_path = (
        market_event_relationships.get("summary_rel_path") or market_event_payload.get("summary_rel_path")
    )
    source_registry_rel_path = (
        source_registry_relationships.get("summary_rel_path") or source_registry_payload.get("summary_rel_path")
    )
    deep_analysis_rel_path = (
        deep_analysis_relationships.get("summary_rel_path") or deep_analysis_payload.get("summary_rel_path")
    )
    market_flow_rel_path = (
        market_flow_relationships.get("summary_rel_path") or market_flow_payload.get("summary_rel_path")
    )
    opportunity_radar_rel_path = (
        opportunity_radar_relationships.get("summary_rel_path") or opportunity_radar_payload.get("summary_rel_path")
    )
    opportunity_lifecycle_rel_path = (
        opportunity_lifecycle_relationships.get("summary_rel_path")
        or opportunity_lifecycle_payload.get("summary_rel_path")
    )
    strategy_evidence_rel_path = (
        strategy_evidence_relationships.get("summary_rel_path") or strategy_evidence_payload.get("summary_rel_path")
    )
    attack_defense_rel_path = (
        attack_defense_relationships.get("summary_rel_path") or attack_defense_payload.get("summary_rel_path")
    )
    paper_watchlist_rel_path = (
        paper_watchlist_relationships.get("summary_rel_path") or paper_watchlist_payload.get("summary_rel_path")
    )
    paper_performance_rel_path = (
        paper_performance_relationships.get("summary_rel_path")
        or paper_performance_payload.get("summary_rel_path")
    )
    forecast_rel_path = (
        forecast_relationships.get("summary_rel_path") or forecast_payload.get("summary_rel_path")
    )

    dispatch_board_patch_payload = dispatch_board_patch.get("payload") or {}
    dispatch_board_preview_rel_path = dispatch_board_patch_payload.get("dispatch_board_preview_rel_path")
    dispatch_board_display_rel_path = dispatch_board_preview_rel_path or dispatch_board_rel_path
    dispatch_board_display_updated_at = path_timestamp(resolve_project_path(dispatch_board_display_rel_path))
    a_share_trade_date = trades.get("a_share_latest")
    hk_trade_date = trades.get("hk_latest")
    us_trade_date = trades.get("us_latest")
    trade_targets = expected_trade_dates(now)
    a_share_expected_trade_date = format_date(trade_targets["a_expected"])
    hk_expected_trade_date = format_date(trade_targets["hk_expected"])
    us_expected_trade_date = format_date(trade_targets["us_expected"])
    cn_factor_expected_trade_date = format_date(trade_targets["cn_factor_expected"])
    open_positions_by_code = {position.get("ts_code"): position for position in positions["positions"] if position.get("ts_code")}
    forecast_equities = [simplify_forecast_item(item) for item in (forecast_payload.get("equities") or [])]
    forecast_index_proxies = [simplify_forecast_item(item) for item in (forecast_payload.get("index_proxies") or [])]
    forecast_by_symbol = {
        item.get("ts_code"): item for item in forecast_equities if item.get("ts_code")
    }

    key_status = {}
    for entity_type, snapshot in snapshots.items():
        if not snapshot:
            key_status[entity_type] = {
                "entity_id": None,
                "status": "missing",
                "created_at": None,
            }
            continue
        key_status[entity_type] = {
            "entity_id": snapshot.get("entity_id"),
            "status": snapshot.get("status"),
            "created_at": snapshot.get("created_at"),
        }

    state = {
        "generated_at": now.strftime("%Y-%m-%d %H:%M:%S"),
        "project_root": str(ROOT),
        "db_path": relative_to_project(DB_PATH),
        "overview": {
            "today": today.isoformat(),
            "a_share_trade_date": a_share_trade_date,
            "hk_trade_date": hk_trade_date,
            "us_trade_date": us_trade_date,
            "a_share_trade_lag_days": trade_day_lag(
                parse_ymd(a_share_trade_date),
                parse_ymd(a_share_expected_trade_date),
                "A",
            ),
            "hk_trade_lag_days": trade_day_lag(
                parse_ymd(hk_trade_date),
                parse_ymd(hk_expected_trade_date),
                "H",
            ),
            "us_trade_lag_days": trade_day_lag(
                parse_ymd(us_trade_date),
                parse_ymd(us_expected_trade_date),
                "US",
            ),
            "a_share_expected_trade_date": a_share_expected_trade_date,
            "hk_expected_trade_date": hk_expected_trade_date,
            "us_expected_trade_date": us_expected_trade_date,
            "cn_factor_expected_trade_date": cn_factor_expected_trade_date,
            "a_share_expected_gap_days": trade_day_lag(
                parse_ymd(a_share_trade_date),
                parse_ymd(a_share_expected_trade_date),
                "A",
            ),
            "hk_expected_gap_days": trade_day_lag(
                parse_ymd(hk_trade_date),
                parse_ymd(hk_expected_trade_date),
                "H",
            ),
            "us_expected_gap_days": trade_day_lag(
                parse_ymd(us_trade_date),
                parse_ymd(us_expected_trade_date),
                "US",
            ),
            "latest_daily_report_date": latest_report_date,
            "daily_report_lag_days": date_lag_days(latest_report_date, today),
            "open_position_count": positions["open_count"],
            "unacknowledged_alert_count": risks["unacknowledged_alerts"],
            "pool_counts": pools,
            "today_registry_counts": registry_counts,
            "today_script_status_counts": run_log["today_status_counts"],
            "today_script_count": run_log["today_script_count"],
            "key_status": key_status,
        },
        "reporting": {
            "report_surface_date": daily_payload.get("report_surface_date"),
            "latest_report_anchor_date": daily_payload.get("latest_report_anchor_date"),
            "latest_report_is_aligned": daily_payload.get("latest_report_is_aligned"),
            "latest_report_title": daily_payload.get("latest_report_title"),
            "latest_report_summary": daily_payload.get("latest_report_summary"),
            "latest_report_updated_at": daily_payload.get("latest_report_updated_at"),
            "capital_flow_fact_sheet": daily_payload.get("capital_flow_fact_sheet") or capital_flow_fact_sheet,
            "daily_candidate_summary": daily_candidate_payload.get("candidate_summary"),
            "dispatch_board_title": daily_payload.get("dispatch_board_title"),
            "dispatch_board_updated_at": dispatch_board_display_updated_at or daily_payload.get("dispatch_board_updated_at"),
            "report_count": daily_payload.get("report_count"),
            "external_research_digest": {
                "focus_strategy": ((daily_payload.get("external_research_digest") or {}).get("focus_strategy")),
                "focus_count": ((daily_payload.get("external_research_digest") or {}).get("focus_count")),
                "items": [
                    simplify_external_research_item(item)
                    for item in (((daily_payload.get("external_research_digest") or {}).get("items") or [])[:7])
                ],
            },
            "official_material_digest": {
                "focus_strategy": ((daily_payload.get("official_material_digest") or {}).get("focus_strategy")),
                "focus_count": ((daily_payload.get("official_material_digest") or {}).get("focus_count")),
                "items": [
                    simplify_official_material_item(item)
                    for item in (((daily_payload.get("official_material_digest") or {}).get("items") or [])[:7])
                ],
            },
            "public_transcript_digest": {
                "focus_strategy": ((daily_payload.get("public_transcript_digest") or {}).get("focus_strategy")),
                "focus_count": ((daily_payload.get("public_transcript_digest") or {}).get("focus_count")),
                "items": [
                    simplify_public_transcript_item(item)
                    for item in (((daily_payload.get("public_transcript_digest") or {}).get("items") or [])[:7])
                ],
            },
            "public_analyst_signal_digest": {
                "focus_strategy": ((daily_payload.get("public_analyst_signal_digest") or {}).get("focus_strategy")),
                "focus_count": ((daily_payload.get("public_analyst_signal_digest") or {}).get("focus_count")),
                "items": [
                    simplify_public_signal_item(item)
                    for item in (((daily_payload.get("public_analyst_signal_digest") or {}).get("items") or [])[:7])
                ],
            },
            "latest_report": build_artifact(latest_report_rel_path, "最新日报", daily_payload.get("latest_report_summary")),
            "daily_candidate": build_artifact(
                daily_candidate_rel_path,
                "日报候选稿",
                daily_candidate_payload.get("candidate_summary"),
            ),
            "dispatch_board": build_artifact(dispatch_board_display_rel_path, "调度面板"),
            "market_flow_anomaly": {
                "entity_id": market_flow_snapshot.get("entity_id"),
                "status": market_flow_snapshot.get("status"),
                "created_at": market_flow_snapshot.get("created_at"),
                "overview_lines": market_flow_payload.get("overview_lines") or [],
                "coverage_summary": market_flow_payload.get("coverage_summary") or {},
                "markets": {
                    "A": [simplify_market_flow_item(item) for item in (market_flow_payload.get("markets") or {}).get("A", [])],
                    "H": [simplify_market_flow_item(item) for item in (market_flow_payload.get("markets") or {}).get("H", [])],
                    "US": [simplify_market_flow_item(item) for item in (market_flow_payload.get("markets") or {}).get("US", [])],
                },
                "artifact": build_artifact(market_flow_rel_path, "全覆盖库资金异动"),
            },
        },
        "opportunity_engine": {
            "radar": {
                "entity_id": opportunity_radar_snapshot.get("entity_id"),
                "status": opportunity_radar_snapshot.get("status"),
                "created_at": opportunity_radar_snapshot.get("created_at"),
                "mode": opportunity_radar_payload.get("mode"),
                "coverage_summary": opportunity_radar_payload.get("coverage_summary") or {},
                "scored_count": opportunity_radar_payload.get("scored_count") or 0,
                "candidate_count": opportunity_radar_payload.get("candidate_count") or 0,
                "paper_watch_candidate_count": opportunity_radar_payload.get("paper_watch_candidate_count") or 0,
                "overview_lines": opportunity_radar_payload.get("overview_lines") or [],
                "sector_heatmap": opportunity_radar_payload.get("sector_heatmap") or [],
                "markets": opportunity_radar_payload.get("markets") or {},
                "top_candidates": opportunity_radar_payload.get("top_candidates") or [],
                "artifact": build_artifact(opportunity_radar_rel_path, "主动机会雷达"),
            },
            "lifecycle": {
                "entity_id": opportunity_lifecycle_snapshot.get("entity_id"),
                "status": opportunity_lifecycle_snapshot.get("status"),
                "created_at": opportunity_lifecycle_snapshot.get("created_at"),
                "current_candidate_count": opportunity_lifecycle_payload.get("current_candidate_count") or 0,
                "previous_candidate_count": opportunity_lifecycle_payload.get("previous_candidate_count") or 0,
                "state_counts": opportunity_lifecycle_payload.get("state_counts") or {},
                "overview_lines": opportunity_lifecycle_payload.get("overview_lines") or [],
                "items": opportunity_lifecycle_payload.get("items") or [],
                "artifact": build_artifact(opportunity_lifecycle_rel_path, "机会生命周期"),
            },
            "evidence": {
                "entity_id": strategy_evidence_snapshot.get("entity_id"),
                "status": strategy_evidence_snapshot.get("status"),
                "created_at": strategy_evidence_snapshot.get("created_at"),
                "candidate_count": strategy_evidence_payload.get("candidate_count") or 0,
                "ready_count": strategy_evidence_payload.get("ready_count") or 0,
                "overview_lines": strategy_evidence_payload.get("overview_lines") or [],
                "items": strategy_evidence_payload.get("items") or [],
                "artifact": build_artifact(strategy_evidence_rel_path, "策略证据快照"),
            },
            "attack_defense": {
                "entity_id": attack_defense_snapshot.get("entity_id"),
                "status": attack_defense_snapshot.get("status"),
                "created_at": attack_defense_snapshot.get("created_at"),
                "case_count": attack_defense_payload.get("case_count") or 0,
                "paper_watch_ready_count": attack_defense_payload.get("paper_watch_ready_count") or 0,
                "watch_with_evidence_count": attack_defense_payload.get("watch_with_evidence_count") or 0,
                "research_first_count": attack_defense_payload.get("research_first_count") or 0,
                "overview_lines": attack_defense_payload.get("overview_lines") or [],
                "cases": attack_defense_payload.get("cases") or [],
                "artifact": build_artifact(attack_defense_rel_path, "机会攻防推演"),
            },
            "paper_watchlist": {
                "entity_id": paper_watchlist_snapshot.get("entity_id"),
                "status": paper_watchlist_snapshot.get("status"),
                "created_at": paper_watchlist_snapshot.get("created_at"),
                "mode": paper_watchlist_payload.get("mode"),
                "live_trading_enabled": paper_watchlist_payload.get("live_trading_enabled"),
                "ticket_count": paper_watchlist_payload.get("ticket_count") or 0,
                "overview_lines": paper_watchlist_payload.get("overview_lines") or [],
                "tickets": paper_watchlist_payload.get("tickets") or [],
                "artifact": build_artifact(paper_watchlist_rel_path, "纸面机会观察单"),
            },
            "paper_performance": {
                "entity_id": paper_performance_snapshot.get("entity_id"),
                "status": paper_performance_snapshot.get("status"),
                "created_at": paper_performance_snapshot.get("created_at"),
                "evaluated_ticket_count": paper_performance_payload.get("evaluated_ticket_count") or 0,
                "status_counts": paper_performance_payload.get("status_counts") or {},
                "overview_lines": paper_performance_payload.get("overview_lines") or [],
                "items": paper_performance_payload.get("items") or [],
                "artifact": build_artifact(paper_performance_rel_path, "纸面观察表现复盘"),
            },
        },
        "deep_analysis": {
            "entity_id": deep_analysis_snapshot.get("entity_id"),
            "status": deep_analysis_snapshot.get("status"),
            "created_at": deep_analysis_snapshot.get("created_at"),
            "cadence_hours": deep_analysis_payload.get("cadence_hours"),
            "theme_count": deep_analysis_payload.get("theme_count"),
            "target_count": deep_analysis_payload.get("target_count"),
            "evaluated_count": deep_analysis_payload.get("evaluated_count"),
            "a_share_candidate_count": deep_analysis_payload.get("a_share_candidate_count") or 0,
            "us_candidate_count": deep_analysis_payload.get("us_candidate_count") or 0,
            "overview_lines": deep_analysis_payload.get("overview_lines") or [],
            "theme_radar": deep_analysis_payload.get("theme_radar") or [],
            "a_share_candidates": [
                simplify_deep_candidate_item(item) for item in (deep_analysis_payload.get("a_share_candidates") or [])
            ],
            "us_candidates": [
                simplify_deep_candidate_item(item) for item in (deep_analysis_payload.get("us_candidates") or [])
            ],
            "coverage_gaps": deep_analysis_payload.get("coverage_gaps") or [],
            "artifact": build_artifact(deep_analysis_rel_path, "深度市场分析"),
        },
        "analysis_forecast": {
            "entity_id": forecast_snapshot.get("entity_id"),
            "status": forecast_snapshot.get("status"),
            "created_at": forecast_snapshot.get("created_at"),
            "batch_date": forecast_payload.get("batch_date"),
            "methodology": forecast_payload.get("methodology"),
            "note": forecast_payload.get("note"),
            "coverage_summary": forecast_payload.get("coverage_summary") or {},
            "overview_lines": forecast_payload.get("overview_lines") or [],
            "equity_count": forecast_payload.get("equity_count") or 0,
            "index_proxy_count": forecast_payload.get("index_proxy_count") or 0,
            "all_equities": forecast_equities,
            "equities_by_market": {
                "A": [item for item in forecast_equities if item.get("market") == "A"],
                "H": [item for item in forecast_equities if item.get("market") == "H"],
                "US": [item for item in forecast_equities if item.get("market") == "US"],
            },
            "index_proxies": forecast_index_proxies,
            "artifact": build_artifact(forecast_rel_path, "价格区间推演快照"),
        },
        "strategy_watch": {
            "entity_id": strategy_watch.get("entity_id"),
            "status": strategy_watch.get("status"),
            "created_at": strategy_watch.get("created_at"),
            "focus_strategy": strategy_payload.get("focus_strategy"),
            "item_count": strategy_payload.get("item_count"),
            "priority_counts": strategy_payload.get("priority_counts") or {},
            "top_focus_items": [simplify_watch_item(item) for item in (strategy_payload.get("top_focus_items") or [])],
            "all_items": [simplify_watch_item(item) for item in (strategy_payload.get("items") or [])],
            "artifact": build_artifact(strategy_rel_path, "策略观察批次"),
        },
        "rotation": {
            "entity_id": rotation.get("entity_id"),
            "status": rotation.get("status"),
            "created_at": rotation.get("created_at"),
            "holdings_reference_count": rotation_payload.get("holdings_reference_count"),
            "opportunity_count": rotation_payload.get("opportunity_count"),
            "rotation_pair_count": rotation_payload.get("rotation_pair_count"),
            "top_add_candidates": [simplify_watch_item(item) for item in (rotation_payload.get("top_add_candidates") or [])[:5]],
            "top_reduce_candidates": [
                simplify_watch_item(item) for item in (rotation_payload.get("top_reduce_candidates") or [])[:5]
            ],
            "rotation_pairs": [simplify_rotation_pair(item) for item in (rotation_payload.get("rotation_pairs") or [])[:5]],
            "artifact": build_artifact(rotation_rel_path, "轮动候选快照"),
            "execution_plan_artifact": build_artifact(execution_rel_path, "轮动执行计划"),
        },
        "portfolio_action": {
            "entity_id": action_memo.get("entity_id"),
            "status": action_memo.get("status"),
            "created_at": action_memo.get("created_at"),
            "action_mode": action_payload.get("action_mode"),
            "action_count": action_payload.get("action_count"),
            "priority_counts": action_payload.get("priority_counts") or {},
            "action_type_counts": action_payload.get("action_type_counts") or {},
            "execution_precheck_status": action_payload.get("execution_precheck_status"),
            "primary_call": (action_payload.get("primary_call") or [])[:5],
            "actions": [simplify_action(item) for item in (action_payload.get("actions") or [])],
            "artifact": build_artifact(action_rel_path, "组合动作建议"),
            "action_log_artifact": build_artifact(action_payload.get("action_log_rel_path"), "组合动作日志"),
            "execution_precheck_artifact": build_artifact(precheck_rel_path, "执行前检查"),
        },
        "risk": {
            "entity_id": risk_snapshot.get("entity_id"),
            "status": risk_snapshot.get("status"),
            "created_at": risk_snapshot.get("created_at"),
            "snapshot_alert_count": risk_payload.get("alert_count"),
            "snapshot_open_position_count": risk_payload.get("open_position_count"),
            "snapshot_unacknowledged_alert_count": risk_payload.get("unacknowledged_alert_count"),
            "severity_counts": risks["severity_counts"],
            "recent_alerts": risks["recent_alerts"],
            "open_positions": positions["positions"],
            "decision": {
                "entity_id": risk_decision_snapshot.get("entity_id"),
                "status": risk_decision_snapshot.get("status"),
                "created_at": risk_decision_snapshot.get("created_at"),
                "portfolio_mode": risk_decision_payload.get("portfolio_mode"),
                "portfolio_state": risk_decision_payload.get("portfolio_state"),
                "portfolio_state_label": risk_decision_payload.get("portfolio_state_label"),
                "portfolio_buy_call": risk_decision_payload.get("portfolio_buy_call"),
                "portfolio_sell_call": risk_decision_payload.get("portfolio_sell_call"),
                "portfolio_constraints": risk_decision_payload.get("portfolio_constraints") or [],
                "headline_actions": risk_decision_payload.get("headline_actions") or [],
                "buy_candidate_count": risk_decision_payload.get("buy_candidate_count") or 0,
                "sell_candidate_count": risk_decision_payload.get("sell_candidate_count") or 0,
                "buy_candidates": risk_decision_payload.get("buy_candidates") or [],
                "sell_candidates": risk_decision_payload.get("sell_candidates") or [],
                "artifact": build_artifact(risk_decision_rel_path, "买卖决策风控"),
            },
        },
        "capital_flow": {
            "fact_sheet": capital_flow_fact_sheet,
            "margin_balance": {
                "entity_id": margin_snapshot.get("entity_id"),
                "status": margin_snapshot.get("status"),
                "created_at": margin_snapshot.get("created_at"),
                "anchor_trade_date": margin_payload.get("anchor_trade_date"),
                "requested_anchor_trade_date": margin_payload.get("requested_anchor_trade_date"),
                "exchange_trade_dates": margin_payload.get("resolved_trade_dates") or {},
                "fact_summary_line": ((capital_flow_fact_sheet.get("margin_balance") or {}).get("summary_line")),
                "metric_note": ((capital_flow_fact_sheet.get("margin_balance") or {}).get("metric_note")),
                "detail_row_count": margin_payload.get("detail_row_count"),
                "active_universe_hit_count": margin_payload.get("active_universe_hit_count"),
                "active_universe_missing_count": margin_payload.get("active_universe_missing_count"),
                "counts_by_exchange": margin_payload.get("counts_by_exchange") or {},
                "focus_hits": margin_focus_hits,
                "artifact": build_artifact(margin_rel_path, "两融快照"),
            },
            "stock_connect": {
                "entity_id": stock_connect_snapshot.get("entity_id"),
                "status": stock_connect_snapshot.get("status"),
                "created_at": stock_connect_snapshot.get("created_at"),
                "anchor_trade_date": stock_connect_payload.get("anchor_trade_date"),
                "requested_anchor_trade_date": stock_connect_payload.get("requested_anchor_trade_date"),
                "market_trade_dates": stock_connect_payload.get("market_trade_dates") or {},
                "holding_trade_dates": stock_connect_payload.get("holding_trade_dates") or {},
                "fact_summary_line": ((capital_flow_fact_sheet.get("stock_connect") or {}).get("summary_line")),
                "holding_summary_line": ((capital_flow_fact_sheet.get("stock_connect") or {}).get("holding_line")),
                "probe_line": ((capital_flow_fact_sheet.get("stock_connect") or {}).get("probe_line")),
                "estimate_line": ((capital_flow_fact_sheet.get("stock_connect") or {}).get("estimate_line")),
                "metric_note": ((capital_flow_fact_sheet.get("stock_connect") or {}).get("metric_note")),
                "holding_row_count": stock_connect_payload.get("holding_row_count"),
                "active_universe_hit_count": stock_connect_payload.get("active_universe_hit_count"),
                "active_universe_missing_count": stock_connect_payload.get("active_universe_missing_count"),
                "market_summary_count": stock_connect_payload.get("market_summary_count"),
                "holding_counts_by_route": stock_connect_payload.get("holding_counts_by_route") or {},
                "route_realtime_probe": stock_connect_payload.get("route_realtime_probe") or {},
                "northbound_estimate_summary": stock_connect_payload.get("northbound_estimate_summary") or [],
                "focus_hits": stock_connect_focus_hits,
                "market_summaries": stock_connect_market_summaries,
                "artifact": build_artifact(stock_connect_rel_path, "互联互通快照"),
            },
        },
        "events": {
            "market_event_snapshot": {
                "entity_id": market_event_snapshot.get("entity_id"),
                "status": market_event_snapshot.get("status"),
                "created_at": market_event_snapshot.get("created_at"),
                "event_count": market_event_payload.get("event_count"),
                "counts_by_family": market_event_payload.get("counts_by_family") or {},
                "artifact": build_artifact(market_event_rel_path, "事件归一化快照"),
            },
            "event_calendar_snapshot": {
                "entity_id": event_calendar_snapshot.get("entity_id"),
                "status": event_calendar_snapshot.get("status"),
                "created_at": event_calendar_snapshot.get("created_at"),
                "event_count": event_calendar_payload.get("event_count"),
                "upcoming_event_count": event_calendar_payload.get("upcoming_event_count"),
                "tracked_symbol_count": event_calendar_payload.get("tracked_symbol_count"),
                "lookback_days": event_calendar_payload.get("lookback_days"),
                "artifact": build_artifact(event_calendar_rel_path, "事件日历快照"),
            },
            "upcoming_event_calendar_snapshot": {
                "entity_id": upcoming_event_calendar_snapshot.get("entity_id"),
                "status": upcoming_event_calendar_snapshot.get("status"),
                "created_at": upcoming_event_calendar_snapshot.get("created_at"),
                "upcoming_event_count": upcoming_event_calendar_payload.get("upcoming_event_count"),
                "days_forward": upcoming_event_calendar_payload.get("days_forward"),
                "artifact": build_artifact(upcoming_event_calendar_rel_path, "未来催化抽取快照"),
            },
            "recent_market_events": market_events,
            "recent_market_events_by_family": market_events_by_family,
            "upcoming_market_events": upcoming_events,
        },
        "source_registry": {
            "entity_id": source_registry_snapshot.get("entity_id"),
            "status": source_registry_snapshot.get("status"),
            "created_at": source_registry_snapshot.get("created_at"),
            "source_count": source_registry_payload.get("source_count"),
            "counts_by_layer": source_registry_payload.get("counts_by_layer") or {},
            "counts_by_status": source_registry_payload.get("counts_by_status") or {},
            "artifact": build_artifact(source_registry_rel_path, "输入源登记快照"),
        },
        "detail_context": {
            "by_ts_code": {
                ts_code: {
                    "recent_events": detail_market_events.get(ts_code) or [],
                    "upcoming_events": detail_upcoming_events.get(ts_code) or [],
                    "margin_balance": detail_margin_hits.get(ts_code),
                    "stock_connect_hits": detail_stock_connect_hits.get(ts_code) or [],
                    "capital_flow_fact_sheet": capital_flow_fact_sheet,
                    "risk_alerts": detail_risk_alerts.get(ts_code) or [],
                    "external_research": detail_external_research.get(ts_code),
                    "official_material": detail_official_materials.get(ts_code) or {},
                    "public_transcript": detail_public_transcripts.get(ts_code),
                    "open_position": open_positions_by_code.get(ts_code),
                    "forecast": forecast_by_symbol.get(ts_code),
                }
                for ts_code in detail_symbol_list
            }
        },
        "operations": {
            "registry_timeline": timeline,
            "run_log": run_log,
            "scheduler": scheduler,
        },
    }
    state["state_version"] = build_state_version(state)
    return state
