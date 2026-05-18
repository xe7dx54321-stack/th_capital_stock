#!/usr/bin/env python3
"""Sync watchlist and portfolio holdings registries into the stock_pool table as coverage universe."""

import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_paths import project_path
from smr_runlog import log_run
from smr_universe import parse_registry_rows

ROOT = project_path()
DB_PATH = project_path("01_data", "db", "smr.db")
WATCHLIST_PATH = project_path("00_control", "watchlist_registry.md")
PORTFOLIO_HOLDINGS_PATH = project_path("00_control", "portfolio_holdings_registry.md")
OUTPUT_DIR = project_path("03_stock_pool", "watchlist")


def normalize_ah_code(raw_code, market):
    code = raw_code.strip()
    if market == "HK":
        return f"{code}.HK"
    if code.startswith(("0", "3")):
        return f"{code}.SZ"
    if code.startswith(("4", "8")):
        return f"{code}.BJ"
    return f"{code}.SH"


def ensure_pool_views(conn):
    conn.executescript(
        """
        DROP VIEW IF EXISTS stock_pool_latest;
        CREATE VIEW stock_pool_latest AS
        WITH ranked AS (
            SELECT
                rowid AS event_rowid,
                pool_type,
                ts_code,
                sector,
                added_date,
                added_reason,
                score,
                status,
                ROW_NUMBER() OVER (
                    PARTITION BY pool_type, ts_code
                    ORDER BY datetime(added_date) DESC, rowid DESC
                ) AS rn
            FROM stock_pool
        )
        SELECT
            pool_type,
            ts_code,
            sector,
            added_date,
            added_reason,
            score,
            status
        FROM ranked
        WHERE rn = 1;

        DROP VIEW IF EXISTS stock_pool_current;
        CREATE VIEW stock_pool_current AS
        SELECT
            pool_type,
            ts_code,
            sector,
            added_date,
            added_reason,
            score,
            status
        FROM stock_pool_latest
        WHERE status = 'active';
        """
    )


def parse_watchlist_registry():
    rows = []
    for row in parse_registry_rows():
        synced = dict(row)
        synced["status"] = "active"
        rows.append(synced)
    return rows


def write_snapshot(rows, synced_at):
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    snapshot_path = OUTPUT_DIR / f"{synced_at[:10]}_seed_sync.md"
    lines = [
        "# SMR Seed Universe Sync",
        "",
        f"- synced_at: {synced_at}",
        f"- source: {WATCHLIST_PATH}",
        f"- extra_source: {PORTFOLIO_HOLDINGS_PATH}",
        f"- rows: {len(rows)}",
        "",
        "| pool_type | ts_code | name | sector | registry_added |",
        "|-----------|---------|------|--------|----------------|",
    ]
    for row in rows:
        lines.append(
            f"| {row['pool_type']} | {row['ts_code']} | {row['name']} | {row['sector']} | {row['registry_added']} |"
        )
    snapshot_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return snapshot_path


def upsert_seed_rows(conn, rows, event_time):
    for row in rows:
        source_name = WATCHLIST_PATH.name
        if row["pool_type"] == "portfolio_seed":
            source_name = PORTFOLIO_HOLDINGS_PATH.name
        conn.execute(
            """
            INSERT OR REPLACE INTO stock_pool
            (pool_type, ts_code, sector, added_date, added_reason, score, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row["pool_type"],
                row["ts_code"],
                row["sector"],
                event_time,
                f"seed sync from {source_name} (registry_added={row['registry_added']})",
                None,
                row["status"],
            ),
        )


def deactivate_removed_seed_rows(conn, current_rows, event_time):
    for pool_type in ("seed", "portfolio_seed"):
        current_codes = {row["ts_code"] for row in current_rows if row["pool_type"] == pool_type}
        latest_codes = {
            code
            for (code,) in conn.execute(
                "SELECT ts_code FROM stock_pool_latest WHERE pool_type=? AND status='active'",
                (pool_type,),
            ).fetchall()
        }
        removed_codes = sorted(latest_codes - current_codes)
        for ts_code in removed_codes:
            sector = conn.execute(
                "SELECT sector FROM stock_pool_latest WHERE pool_type=? AND ts_code=?",
                (pool_type, ts_code),
            ).fetchone()
            conn.execute(
                """
                INSERT OR REPLACE INTO stock_pool
                (pool_type, ts_code, sector, added_date, added_reason, score, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pool_type,
                    ts_code,
                    sector[0] if sector else None,
                    event_time,
                    f"removed from {PORTFOLIO_HOLDINGS_PATH.name if pool_type == 'portfolio_seed' else WATCHLIST_PATH.name}",
                    None,
                    "inactive",
                ),
            )


def main():
    rows = parse_watchlist_registry()
    if not rows:
        raise SystemExit("No rows parsed from coverage registries")

    synced_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    event_time = synced_at

    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        UPDATE stock_pool
        SET pool_type='seed'
        WHERE pool_type='watchlist'
          AND added_reason='seeded from watchlist_registry.md'
        """
    )
    ensure_pool_views(conn)
    deactivate_removed_seed_rows(conn, rows, event_time)
    upsert_seed_rows(conn, rows, event_time)
    ensure_pool_views(conn)
    conn.commit()
    conn.close()

    snapshot_path = write_snapshot(rows, synced_at)
    seed_count = len([row for row in rows if row["pool_type"] == "seed"])
    portfolio_seed_count = len([row for row in rows if row["pool_type"] == "portfolio_seed"])
    us_count = len([row for row in rows if row["pool_type"] == "us_benchmark"])
    log_run(
        "sync_watchlist.py",
        "success",
        "coverage universe synced",
        {
            "seed": seed_count,
            "portfolio_seed": portfolio_seed_count,
            "us_benchmark": us_count,
            "snapshot": str(snapshot_path),
        },
    )
    print(
        "Synced coverage universe into stock_pool: "
        f"seed={seed_count}, portfolio_seed={portfolio_seed_count}, us_benchmark={us_count}"
    )
    print(f"Snapshot: {snapshot_path}")


if __name__ == "__main__":
    main()
