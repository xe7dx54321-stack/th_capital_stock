#!/usr/bin/env python3
"""Register an ad-hoc task registry snapshot."""

import argparse
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_paths import project_path
from smr_registry import register_snapshot
from smr_wiki import loads_json

DB_PATH = project_path("01_data", "db", "smr.db")


def parse_json(text):
    if not text:
        return {}
    parsed = loads_json(text, None)
    if parsed is None:
        raise SystemExit("Invalid JSON payload")
    return parsed


def main():
    parser = argparse.ArgumentParser(description="Register an ad-hoc SMR task registry snapshot")
    parser.add_argument("--entity-type", required=True)
    parser.add_argument("--entity-id", required=True)
    parser.add_argument("--status", required=True)
    parser.add_argument("--source", required=True)
    parser.add_argument("--relationships", help="JSON object")
    parser.add_argument("--payload", help="JSON object")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    entry = register_snapshot(
        conn,
        entity_type=args.entity_type,
        entity_id=args.entity_id,
        status=args.status,
        source=args.source,
        relationships=parse_json(args.relationships),
        payload=parse_json(args.payload),
    )
    conn.commit()
    conn.close()
    print(entry["id"])


if __name__ == "__main__":
    main()
