#!/usr/bin/env python3
"""Apply approved recommendations to the paper portfolio lifecycle."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_paper_portfolio import apply_approved_recommendations
from smr_registry import register_snapshot
from smr_runlog import log_run

SCRIPT_NAME = "apply_approved_recommendations_to_paper_portfolio.py"


def main() -> int:
    parser = argparse.ArgumentParser(description="Create paper orders/positions from approved recommendations")
    parser.add_argument("--limit", type=int, default=100)
    parser.add_argument("--no-execute", action="store_true", help="Create orders but do not execute eligible paper orders")
    parser.add_argument("--max-price-age-days", type=int, default=7)
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    try:
        result = apply_approved_recommendations(
            conn,
            limit=args.limit,
            execute=not args.no_execute,
            max_price_age_days=args.max_price_age_days,
        )
        register_snapshot(
            conn,
            entity_type="paper_portfolio_application",
            entity_id="latest",
            status="updated",
            source=SCRIPT_NAME,
            payload=result,
        )
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "approved recommendations applied to paper portfolio", result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
