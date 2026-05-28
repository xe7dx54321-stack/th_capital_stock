#!/usr/bin/env python3
"""Build Phase 42 official consensus fulfillment report."""

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
from smr_official_consensus_fulfillment import build_official_consensus_fulfillment

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(conn: sqlite3.Connection, ticker: str) -> dict:
    return build_official_consensus_fulfillment(conn, ticker)


def render_markdown(payload: dict) -> str:
    body = payload.get("official_consensus_fulfillment") or {}
    lines = [f"# Phase 42 Official Consensus Fulfillment: {payload.get('ticker')}", ""]
    for key in ("request_status", "availability_status", "fulfillment_status", "authorized_source_required", "internal_proxy_allowed"):
        lines.append(f"- {key}: {body.get(key)}")
    lines.extend(["", "## Required Fields"])
    lines.extend(f"- {item}" for item in body.get("required_fields") or [])
    lines.extend(["", "## Do Not Do"])
    lines.extend(f"- {item}" for item in body.get("do_not_do") or [])
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 42 official consensus fulfillment")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker", default="300308.SZ")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, args.ticker)
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload), end="")
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
