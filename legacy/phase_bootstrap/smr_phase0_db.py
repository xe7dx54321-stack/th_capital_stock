#!/usr/bin/env python3
"""Phase 0-2: Initialize SMR SQLite database with all tables + sector_config seed data."""

import sqlite3
import os

DB_PATH = "/Users/apple/Documents/同行资本二级市场/01_data/db/smr.db"
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.executescript("""
CREATE TABLE IF NOT EXISTS daily_bar (
    ts_code    TEXT NOT NULL,
    trade_date TEXT NOT NULL,
    open       REAL,
    close      REAL,
    high       REAL,
    low        REAL,
    vol        REAL,
    amount     REAL,
    pct_chg    REAL,
    turnover   REAL,
    market     TEXT DEFAULT 'A',
    PRIMARY KEY (ts_code, trade_date)
);

CREATE TABLE IF NOT EXISTS us_daily_bar (
    symbol     TEXT NOT NULL,
    trade_date TEXT NOT NULL,
    open       REAL,
    close      REAL,
    high       REAL,
    low        REAL,
    vol        REAL,
    amount     REAL,
    pct_chg    REAL,
    PRIMARY KEY (symbol, trade_date)
);

CREATE TABLE IF NOT EXISTS us_signal (
    signal_id   INTEGER PRIMARY KEY AUTOINCREMENT,
    signal_time TEXT NOT NULL,
    symbol      TEXT NOT NULL,
    signal_type TEXT NOT NULL,
    title       TEXT,
    summary     TEXT,
    ah_impact   TEXT,
    related_ah  TEXT,
    source_url  TEXT,
    created_at  TEXT
);

CREATE TABLE IF NOT EXISTS factor_daily (
    ts_code     TEXT NOT NULL,
    trade_date  TEXT NOT NULL,
    factor_name TEXT NOT NULL,
    factor_value REAL,
    PRIMARY KEY (ts_code, trade_date, factor_name)
);

CREATE TABLE IF NOT EXISTS stock_pool (
    pool_type   TEXT NOT NULL,
    ts_code     TEXT NOT NULL,
    sector      TEXT,
    added_date  TEXT NOT NULL,
    added_reason TEXT,
    score       REAL,
    status      TEXT DEFAULT 'active',
    PRIMARY KEY (pool_type, ts_code, added_date)
);

CREATE TABLE IF NOT EXISTS position (
    ts_code      TEXT NOT NULL,
    entry_date   TEXT NOT NULL,
    entry_price  REAL,
    shares       INTEGER,
    cost         REAL,
    target_price REAL,
    stop_loss    REAL,
    thesis       TEXT,
    exit_date    TEXT,
    exit_price   REAL,
    pnl          REAL,
    pnl_pct      REAL,
    status       TEXT DEFAULT 'open',
    PRIMARY KEY (ts_code, entry_date)
);

CREATE TABLE IF NOT EXISTS risk_alert (
    alert_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    alert_time   TEXT NOT NULL,
    alert_type   TEXT NOT NULL,
    severity     TEXT NOT NULL,
    ts_code      TEXT,
    message      TEXT,
    action       TEXT,
    acknowledged INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS research_index (
    report_id   TEXT PRIMARY KEY,
    report_type TEXT NOT NULL,
    sector      TEXT,
    title       TEXT,
    ts_codes    TEXT,
    created_at  TEXT,
    file_path   TEXT
);

CREATE TABLE IF NOT EXISTS sector_config (
    sector_key     TEXT PRIMARY KEY,
    sector_name    TEXT NOT NULL,
    vcr_priority   TEXT,
    smr_focus      TEXT,
    ah_universe    TEXT,
    us_benchmarks  TEXT
);
""")

sector_data = [
    (
        "embodied_ai",
        "具身智能/机器人",
        "P0-core-build",
        "core_trade",
        "688017,300124,601689,002050,603728,002796,301368,688322,002600,600580,9880.HK",
        "TSLA"
    ),
    (
        "semiconductor_compute",
        "半导体/算力芯片",
        "P1-priority-track",
        "core_trade",
        "688041,688256,688008,301269,688521,603986",
        "NVDA,AMD,INTC,AVGO,SNPS,CDNS,MU"
    ),
    (
        "semiconductor_photonics",
        "半导体/光芯片CPO",
        "P1-priority-track",
        "core_trade",
        "300308,300502,300394,002281,300620,872808,002837",
        "LITE,MRVL,COHR,VRT"
    ),
    (
        "ai_agent",
        "AI Agent/应用",
        "P1-priority-track",
        "watch_observe",
        "002230,688111,0020.HK,603039",
        "CRM,NOW,MSFT"
    ),
    (
        "quantum",
        "量子/前沿科学",
        "P1-priority-track",
        "watch_observe",
        "688027",
        "IONQ,RGTI,QBTS"
    ),
]

cur.executemany(
    "INSERT OR REPLACE INTO sector_config (sector_key, sector_name, vcr_priority, smr_focus, ah_universe, us_benchmarks) VALUES (?,?,?,?,?,?)",
    sector_data,
)

conn.commit()

for table in ["daily_bar", "us_daily_bar", "us_signal", "factor_daily", "stock_pool", "position", "risk_alert", "research_index", "sector_config"]:
    count = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    print(f"  {table}: {count} rows")

conn.close()
print(f"\nDatabase initialized at {DB_PATH}")
