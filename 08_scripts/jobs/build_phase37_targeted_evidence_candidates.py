#!/usr/bin/env python3
"""Build Phase 37 targeted evidence candidates."""

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
from smr_registry import register_snapshot
from smr_targeted_evidence_candidate_builder import build_targeted_evidence_candidates

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


def build_payload(
    conn: sqlite3.Connection,
    *,
    ticker: str,
    limit: int | None = None,
    task_id: str | None = None,
    mode: str = "dry_run",
) -> dict:
    return build_targeted_evidence_candidates(conn, ticker, limit=limit, task_id=task_id, mode=mode)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 37 targeted evidence candidates")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker", required=True)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--task-id")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    mode = "execute" if args.execute and not args.dry_run else "dry_run"
    conn = sqlite3.connect(args.db_path)
    try:
        payload = build_payload(conn, ticker=args.ticker, limit=args.limit, task_id=args.task_id, mode=mode)
        if mode == "execute":
            conn.commit()
            register_snapshot(conn, "phase37_targeted_evidence_candidates", args.ticker, mode, Path(__file__).name, payload=payload)
            conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
