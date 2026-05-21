#!/usr/bin/env python3
"""Update lightweight outcome prices for approved/observation recommendations."""

from __future__ import annotations

import argparse
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_data_health import check_freshness_gate
from smr_decision import ensure_decision_tables
from smr_runlog import log_run

SCRIPT_NAME = "update_decision_outcomes.py"


def relation_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name=?", (name,)).fetchone()
    return bool(row)


def price_on_or_after(conn: sqlite3.Connection, ticker: str, target_date: str, market: str | None) -> float | None:
    table = "us_daily_bar" if market == "US" else "daily_bar"
    if not relation_exists(conn, table):
        return None
    columns = {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}
    ticker_column = "ts_code" if "ts_code" in columns else "symbol"
    row = conn.execute(
        f"SELECT close FROM {table} WHERE {ticker_column}=? AND trade_date>=? ORDER BY trade_date ASC LIMIT 1",
        (ticker, target_date),
    ).fetchone()
    return float(row[0]) if row and row[0] is not None else None


def update_outcomes(conn: sqlite3.Connection, limit: int = 200) -> dict[str, int]:
    ensure_decision_tables(conn)
    gate = check_freshness_gate(conn, "paper_performance", ["daily_bar"], allow_degraded=False)
    if gate.status == "block":
        conn.execute(
            """
            UPDATE decision_ledger
            SET performance_update_status='skipped', performance_update_reason=?, updated_at=?
            WHERE status IN ('approved_paper', 'observation_only')
            """,
            ("daily_bar stale or missing; performance update skipped", datetime.now().strftime("%Y-%m-%d %H:%M:%S")),
        )
        return {"updated": 0, "skipped": conn.total_changes}
    rows = conn.execute(
        """
        SELECT recommendation_id, ticker, market, decision_time, status
        FROM decision_ledger
        WHERE status IN ('approved_paper', 'observation_only')
          AND ticker IS NOT NULL
        ORDER BY datetime(updated_at) DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()
    updated = 0
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for rec_id, ticker, market, decision_time, _status in rows:
        base = datetime.fromisoformat(str(decision_time)[:19]).date()
        p1d = price_on_or_after(conn, ticker, (base + timedelta(days=1)).isoformat(), market)
        p1w = price_on_or_after(conn, ticker, (base + timedelta(days=7)).isoformat(), market)
        p1m = price_on_or_after(conn, ticker, (base + timedelta(days=30)).isoformat(), market)
        p3m = price_on_or_after(conn, ticker, (base + timedelta(days=90)).isoformat(), market)
        conn.execute(
            """
            UPDATE decision_ledger
            SET outcome_price_1d=?, outcome_price_1w=?, outcome_price_1m=?, outcome_price_3m=?,
                performance_update_status='updated', performance_update_reason=NULL, updated_at=?
            WHERE recommendation_id=?
            """,
            (p1d, p1w, p1m, p3m, now, rec_id),
        )
        updated += 1
    return {"updated": updated, "skipped": 0}


def main() -> None:
    parser = argparse.ArgumentParser(description="Update decision outcome prices")
    parser.add_argument("--limit", type=int, default=200)
    args = parser.parse_args()
    conn = sqlite3.connect(DB_PATH)
    try:
        result = update_outcomes(conn, limit=args.limit)
        conn.commit()
    finally:
        conn.close()
    log_run(SCRIPT_NAME, "success", "decision outcomes updated", result)
    print(result)


if __name__ == "__main__":
    main()
