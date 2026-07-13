#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
注册持仓复盘快照
"""
import sys
from pathlib import Path

# 添加lib目录到路径
LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

import json
from datetime import datetime

from smr_registry import register_snapshot
import sqlite3

DB_PATH = 'th_capital_stock/01_data/db/smr.db'

def main():
    conn = sqlite3.connect(DB_PATH)

    payload = {
        "report_path": "th_capital_stock/04_portfolio/performance/daily_2026-06-29.md",
        "actions": {
            "reduce": ["NVDA"],
            "stop_loss": [],
            "partial_profit": []
        },
        "constraints": {
            "single_position": "51.8% (limit: 25%)",
            "sector_concentration": "100% (limit: 50%)",
            "total_exposure": "89.8% (limit: 90%)"
        },
        "total_pnl": -3567.51,
        "position_count": 2
    }

    result = register_snapshot(
        conn,
        entity_type="portfolio_review_snapshot",
        entity_id="20260629",
        status="completed",
        source="TRAE_Portfolio_Review",
        relationships={},
        payload=payload
    )

    print(f"快照注册结果: {result}")
    conn.close()

if __name__ == '__main__':
    main()
