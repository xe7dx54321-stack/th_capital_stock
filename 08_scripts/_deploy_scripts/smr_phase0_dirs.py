#!/usr/bin/env python3
"""Phase 0-1: Create SMR root directory structure."""

import os

ROOT = "/Users/apple/Documents/同行资本二级市场"

DIRS = [
    "00_control",
    "01_data/db",
    "01_data/raw",
    "01_data/factor",
    "01_data/us_signals",
    "02_research/industry/embodied_ai",
    "02_research/industry/semiconductor",
    "02_research/industry/ai_agent",
    "02_research/industry/quantum",
    "02_research/stock",
    "02_research/us_linkage",
    "03_stock_pool/watchlist",
    "03_stock_pool/candidate",
    "03_stock_pool/recommended",
    "04_portfolio/positions",
    "04_portfolio/trades",
    "04_portfolio/performance",
    "05_risk/alerts",
    "05_risk/rules",
    "05_risk/logs",
    "06_reports/daily",
    "06_reports/weekly",
    "06_reports/adhoc",
    "07_publish/queue",
    "07_publish/archive",
    "08_scripts/data_harvester",
    "08_scripts/us_signal_harvester",
    "08_scripts/factor_engine",
    "08_scripts/risk_engine",
    "08_scripts/backtest",
    "08_scripts/portfolio",
    "09_runbooks/scripts",
    "09_runbooks/skills",
    "09_runbooks/templates",
    "10_logs",
]

created = 0
for d in DIRS:
    path = os.path.join(ROOT, d)
    os.makedirs(path, exist_ok=True)
    created += 1

print(f"Created {created} directories under {ROOT}")
