#!/usr/bin/env python3
"""Build live internal consensus proxy signals from evidence_items."""

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
from smr_proxy_extraction import build_live_consensus_proxy
from smr_registry import register_snapshot
from smr_runlog import log_run

SCRIPT_NAME = "build_live_consensus_proxy.py"


def parse_tickers(raw: str | None) -> list[str]:
    return [item.strip() for item in str(raw or "").split(",") if item.strip()]


def main() -> int:
    parser = argparse.ArgumentParser(description="Build live internal consensus proxy")
    parser.add_argument("--tickers", default="NVDA,09988.HK,000001.SZ")
    parser.add_argument("--limit", type=int, default=16)
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    try:
        proxies = [build_live_consensus_proxy(conn, ticker, limit=args.limit) for ticker in parse_tickers(args.tickers)]
        payload = {"proxies": proxies, "proxy_count": len(proxies)}
        register_snapshot(
            conn,
            entity_type="live_consensus_proxy_snapshot",
            entity_id="latest",
            status="success",
            source=SCRIPT_NAME,
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    log_run(SCRIPT_NAME, "success", "live consensus proxy built", {"proxy_count": len(proxies)})
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
