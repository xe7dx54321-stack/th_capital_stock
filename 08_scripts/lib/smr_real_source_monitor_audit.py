#!/usr/bin/env python3
"""Phase 49 real source monitor audit."""

from __future__ import annotations
import sqlite3
from typing import Any
from smr_paper_watchlist_entry import dumps_json, loads_json
from smr_research_review_lifecycle import normalize_ticker
from smr_wiki import generate_execution_id, now_ts

def ensure_real_source_monitor_audit_table(conn: sqlite3.Connection):
    conn.execute("""CREATE TABLE IF NOT EXISTS phase49_real_source_monitor_audit_log (
        audit_id TEXT PRIMARY KEY, ticker TEXT NOT NULL, action TEXT NOT NULL,
        sources_checked INTEGER NOT NULL DEFAULT 0, events_created INTEGER NOT NULL DEFAULT 0,
        events_refreshed INTEGER NOT NULL DEFAULT 0,
        before_watchlist_status TEXT NOT NULL, after_watchlist_status TEXT NOT NULL,
        pending_created INTEGER NOT NULL DEFAULT 0, paper_order_created INTEGER NOT NULL DEFAULT 0,
        real_trade_created INTEGER NOT NULL DEFAULT 0, metadata_json TEXT NOT NULL DEFAULT '{}',
        created_at TEXT NOT NULL)""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_phase49_monitor_audit_ticker ON phase49_real_source_monitor_audit_log(ticker, created_at DESC)")

def write_monitor_audit(conn, *, ticker, action="real_source_event_refresh",
                        sources_checked=0, events_created=0, events_refreshed=0,
                        before_watchlist_status="tracking_strengthened", after_watchlist_status="tracking_strengthened",
                        metadata=None):
    ensure_real_source_monitor_audit_table(conn)
    aid = generate_execution_id(f"audit_real_source_monitor_{normalize_ticker(ticker).split('.')[0]}")
    conn.execute("""INSERT INTO phase49_real_source_monitor_audit_log
        (audit_id,ticker,action,sources_checked,events_created,events_refreshed,before_watchlist_status,after_watchlist_status,pending_created,paper_order_created,real_trade_created,metadata_json,created_at)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (aid, normalize_ticker(ticker), action, sources_checked, events_created, events_refreshed,
         before_watchlist_status, after_watchlist_status, 0,0,0, dumps_json(metadata or {}), now_ts()))
    return get_monitor_audit(conn, aid)

def _r(row): return {"audit_id":row[0],"ticker":row[1],"action":row[2],"sources_checked":row[3],"events_created":row[4],"events_refreshed":row[5],"before_watchlist_status":row[6],"after_watchlist_status":row[7],"pending_created":bool(row[8]),"paper_order_created":bool(row[9]),"real_trade_created":bool(row[10]),"metadata":loads_json(row[11],{}),"created_at":row[12]}

def get_monitor_audit(conn, audit_id):
    ensure_real_source_monitor_audit_table(conn)
    row = conn.execute("SELECT * FROM phase49_real_source_monitor_audit_log WHERE audit_id=? LIMIT 1",(audit_id,)).fetchone()
    return _r(row) if row else {}

def list_monitor_audits(conn, ticker=None):
    ensure_real_source_monitor_audit_table(conn)
    params=[]; where=""
    if ticker: where="WHERE ticker=?"; params.append(normalize_ticker(ticker))
    rows = conn.execute(f"SELECT * FROM phase49_real_source_monitor_audit_log {where} ORDER BY datetime(created_at) DESC",params).fetchall()
    return [_r(r) for r in rows]
