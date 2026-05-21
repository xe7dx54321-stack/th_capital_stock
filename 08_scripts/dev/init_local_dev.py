#!/usr/bin/env python3
"""Initialize an empty local SMR development runtime.

The script is intentionally idempotent. It creates ignored runtime directories
and the minimum SQLite schema/views needed for local tests, dashboard rendering,
dry-runs, and ingestion jobs. It does not seed market prices or investment
conclusions.
"""

from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import ensure_agent_handoff_state_table, ensure_agent_runtime_dirs
from smr_claim_graph import ensure_claim_graph_tables
from smr_consensus_proxy import ensure_consensus_proxy_table
from smr_data_health import ensure_data_health_tables
from smr_decision import ensure_decision_tables
from smr_events import ensure_input_source_registry_table, ensure_market_event_table
from smr_market_flow import ensure_margin_tables, ensure_stock_connect_tables
from smr_paths import env_or_project_path, project_path
from smr_registry import ensure_task_registry_tables
from smr_valuation import ensure_valuation_table
from smr_wiki import (
    ensure_import_execution_table,
    ensure_ingest_draft_table,
    ensure_knowledge_index_table,
    ensure_review_queue_execution_table,
    ensure_source_manifest_table,
)

try:
    from smr_news_ingestion import ensure_news_tables
    from smr_filings_ingestion import ensure_filings_tables
except ImportError:  # pragma: no cover - bootstrap remains usable during partial checkouts.
    ensure_news_tables = None
    ensure_filings_tables = None


DB_PATH = env_or_project_path("SMR_DB_PATH", "01_data", "db", "smr.db")

RUNTIME_DIRS = [
    project_path("01_data", "db"),
    project_path("02_research"),
    project_path("03_stock_pool", "watchlist"),
    project_path("04_portfolio"),
    project_path("05_risk", "alerts"),
    project_path("06_reports", "daily"),
    project_path("10_logs", "scheduler", "runs"),
    project_path("11_smr_wiki", "raw", "manifests"),
    project_path("11_smr_wiki", "raw", "external"),
    project_path("11_smr_wiki", "drafts", "ingest"),
    project_path("11_smr_wiki", "drafts", "review_exports"),
    project_path("11_smr_wiki", "wiki", "sectors"),
    project_path("11_smr_wiki", "wiki", "stocks"),
    project_path("11_smr_wiki", "wiki", "theses"),
    project_path("11_smr_wiki", "wiki", "strategies"),
    project_path("11_smr_wiki", "wiki", "playbooks"),
    project_path("11_smr_wiki", "wiki", "risk_cases"),
    project_path("11_smr_wiki", "wiki", "decisions"),
    project_path("11_smr_wiki", "wiki", "timelines"),
    project_path("12_smr_agents", "handoffs"),
    project_path("12_smr_agents", "workspaces"),
]

SECTOR_DATA = [
    (
        "embodied_ai",
        "Embodied AI / Robotics",
        "P0-core-build",
        "core_trade",
        "688017,300124,601689,002050,603728,002796,301368,688322,002600,600580,9880.HK",
        "TSLA",
    ),
    (
        "semiconductor_compute",
        "Semiconductor / AI Compute",
        "P1-priority-track",
        "core_trade",
        "688041,688256,688008,301269,688521,603986",
        "NVDA,AMD,INTC,AVGO,SNPS,CDNS,MU",
    ),
    (
        "semiconductor_photonics",
        "Semiconductor / Photonics / CPO",
        "P1-priority-track",
        "core_trade",
        "300308,300502,300394,002281,300620,872808,002837",
        "LITE,MRVL,COHR,VRT",
    ),
    (
        "ai_agent",
        "AI Agent / Application",
        "P1-priority-track",
        "watch_observe",
        "002230,688111,0020.HK,603039",
        "CRM,NOW,MSFT",
    ),
    (
        "quantum",
        "Quantum / Frontier Science",
        "P1-priority-track",
        "watch_observe",
        "688027",
        "IONQ,RGTI,QBTS",
    ),
]


def ensure_runtime_dirs() -> None:
    for path in RUNTIME_DIRS:
        path.mkdir(parents=True, exist_ok=True)
    ensure_agent_runtime_dirs()


def ensure_market_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS daily_bar (
            ts_code TEXT NOT NULL,
            trade_date TEXT NOT NULL,
            open REAL,
            close REAL,
            high REAL,
            low REAL,
            vol REAL,
            amount REAL,
            pct_chg REAL,
            turnover REAL,
            market TEXT DEFAULT 'A',
            PRIMARY KEY (ts_code, trade_date)
        );

        CREATE TABLE IF NOT EXISTS us_daily_bar (
            symbol TEXT NOT NULL,
            trade_date TEXT NOT NULL,
            open REAL,
            close REAL,
            high REAL,
            low REAL,
            vol REAL,
            amount REAL,
            pct_chg REAL,
            PRIMARY KEY (symbol, trade_date)
        );

        CREATE TABLE IF NOT EXISTS us_signal (
            signal_id INTEGER PRIMARY KEY AUTOINCREMENT,
            signal_time TEXT NOT NULL,
            symbol TEXT NOT NULL,
            signal_type TEXT NOT NULL,
            title TEXT,
            summary TEXT,
            ah_impact TEXT,
            related_ah TEXT,
            source_url TEXT,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS factor_daily (
            ts_code TEXT NOT NULL,
            trade_date TEXT NOT NULL,
            factor_name TEXT NOT NULL,
            factor_value REAL,
            PRIMARY KEY (ts_code, trade_date, factor_name)
        );

        CREATE TABLE IF NOT EXISTS stock_pool (
            pool_type TEXT NOT NULL,
            ts_code TEXT NOT NULL,
            sector TEXT,
            added_date TEXT NOT NULL,
            added_reason TEXT,
            score REAL,
            status TEXT DEFAULT 'active',
            PRIMARY KEY (pool_type, ts_code, added_date)
        );

        CREATE TABLE IF NOT EXISTS position (
            ts_code TEXT NOT NULL,
            entry_date TEXT NOT NULL,
            entry_price REAL,
            shares INTEGER,
            cost REAL,
            target_price REAL,
            stop_loss REAL,
            thesis TEXT,
            exit_date TEXT,
            exit_price REAL,
            pnl REAL,
            pnl_pct REAL,
            status TEXT DEFAULT 'open',
            PRIMARY KEY (ts_code, entry_date)
        );

        CREATE TABLE IF NOT EXISTS risk_alert (
            alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
            alert_time TEXT NOT NULL,
            alert_type TEXT NOT NULL,
            severity TEXT NOT NULL,
            ts_code TEXT,
            message TEXT,
            action TEXT,
            acknowledged INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS research_index (
            report_id TEXT PRIMARY KEY,
            report_type TEXT NOT NULL,
            sector TEXT,
            title TEXT,
            ts_codes TEXT,
            created_at TEXT,
            file_path TEXT
        );

        CREATE TABLE IF NOT EXISTS sector_config (
            sector_key TEXT PRIMARY KEY,
            sector_name TEXT NOT NULL,
            vcr_priority TEXT,
            smr_focus TEXT,
            ah_universe TEXT,
            us_benchmarks TEXT
        );
        """
    )
    conn.executemany(
        """
        INSERT OR REPLACE INTO sector_config (
            sector_key, sector_name, vcr_priority, smr_focus, ah_universe, us_benchmarks
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        SECTOR_DATA,
    )


def ensure_pool_views(conn: sqlite3.Connection) -> None:
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
        SELECT pool_type, ts_code, sector, added_date, added_reason, score, status
        FROM ranked
        WHERE rn = 1;

        DROP VIEW IF EXISTS stock_pool_current;
        CREATE VIEW stock_pool_current AS
        SELECT pool_type, ts_code, sector, added_date, added_reason, score, status
        FROM stock_pool_latest
        WHERE status = 'active';

        CREATE TABLE IF NOT EXISTS research_decision (
            report_id TEXT PRIMARY KEY,
            ts_code TEXT NOT NULL,
            report_type TEXT NOT NULL,
            sector TEXT,
            title TEXT,
            decision_time TEXT NOT NULL,
            decision_priority INTEGER NOT NULL,
            suggested_pool TEXT NOT NULL,
            thesis_strength TEXT,
            customer_evidence TEXT,
            order_evidence TEXT,
            commercialization_evidence TEXT,
            valuation_risk TEXT,
            open_gap_count INTEGER,
            research_quality_score REAL,
            reason TEXT,
            file_path TEXT
        );

        DROP VIEW IF EXISTS research_decision_latest;
        CREATE VIEW research_decision_latest AS
        WITH ranked AS (
            SELECT
                report_id,
                ts_code,
                report_type,
                sector,
                title,
                decision_time,
                decision_priority,
                suggested_pool,
                thesis_strength,
                customer_evidence,
                order_evidence,
                commercialization_evidence,
                valuation_risk,
                open_gap_count,
                research_quality_score,
                reason,
                file_path,
                ROW_NUMBER() OVER (
                    PARTITION BY ts_code
                    ORDER BY decision_priority DESC, datetime(decision_time) DESC, rowid DESC
                ) AS rn
            FROM research_decision
        )
        SELECT
            report_id,
            ts_code,
            report_type,
            sector,
            title,
            decision_time,
            decision_priority,
            suggested_pool,
            thesis_strength,
            customer_evidence,
            order_evidence,
            commercialization_evidence,
            valuation_risk,
            open_gap_count,
            research_quality_score,
            reason,
            file_path
        FROM ranked
        WHERE rn = 1;
        """
    )


def initialize_database(conn: sqlite3.Connection) -> None:
    ensure_market_schema(conn)
    ensure_pool_views(conn)
    ensure_task_registry_tables(conn)
    ensure_source_manifest_table(conn)
    ensure_ingest_draft_table(conn)
    ensure_knowledge_index_table(conn)
    ensure_import_execution_table(conn)
    ensure_review_queue_execution_table(conn)
    ensure_agent_handoff_state_table(conn)
    ensure_data_health_tables(conn)
    ensure_decision_tables(conn)
    ensure_claim_graph_tables(conn)
    ensure_consensus_proxy_table(conn)
    ensure_valuation_table(conn)
    ensure_input_source_registry_table(conn)
    ensure_market_event_table(conn)
    ensure_margin_tables(conn)
    ensure_stock_connect_tables(conn)
    if ensure_news_tables is not None:
        ensure_news_tables(conn)
    if ensure_filings_tables is not None:
        ensure_filings_tables(conn)


def main() -> int:
    parser = argparse.ArgumentParser(description="Initialize local SMR development runtime")
    parser.add_argument("--db-path", default=str(DB_PATH), help="SQLite database path")
    args = parser.parse_args()

    ensure_runtime_dirs()
    db_path = Path(args.db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    try:
        initialize_database(conn)
        conn.commit()
    finally:
        conn.close()

    print(f"initialized_db={db_path.resolve()}")
    print(f"runtime_dirs={len(RUNTIME_DIRS)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
