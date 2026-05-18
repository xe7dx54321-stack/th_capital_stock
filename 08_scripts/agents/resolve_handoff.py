#!/usr/bin/env python3
"""Resolve an SMR agent handoff."""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH, resolve_handoff
from smr_runlog import log_run


def parse_json_arg(value):
    if value in (None, ""):
        return None
    return json.loads(value)


def main():
    parser = argparse.ArgumentParser(description="Resolve an SMR agent handoff")
    parser.add_argument("handoff_id")
    parser.add_argument("--status", required=True, choices=["accepted", "completed", "rejected", "cancelled"])
    parser.add_argument("--resolved-by", required=True)
    parser.add_argument("--summary")
    parser.add_argument("--outputs-json")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    record = resolve_handoff(
        conn,
        handoff_id=args.handoff_id,
        status=args.status,
        resolved_by=args.resolved_by,
        summary=args.summary,
        outputs=parse_json_arg(args.outputs_json),
    )
    conn.commit()
    conn.close()

    log_run(
        "resolve_handoff.py",
        "success",
        "agent handoff resolved",
        {
            "handoff_id": record["handoff_id"],
            "status": record["status"],
            "resolved_by": args.resolved_by,
        },
    )
    print(f"Resolved handoff: {record['handoff_id']}")
    print(f"Status: {record['status']}")
    print(f"Path: {record['handoff_rel_path']}")


if __name__ == "__main__":
    main()
