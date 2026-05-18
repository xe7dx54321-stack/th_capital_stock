#!/usr/bin/env python3
"""Query task registry entries and entity history."""

import argparse
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_paths import project_path
from smr_registry import get_entity_snapshot, list_entries
from smr_wiki import dumps_json

DB_PATH = project_path("01_data", "db", "smr.db")


def print_entries(entries):
    print("| id | entity_type | entity_id | status | source | snapshot_index | created_at |")
    print("|----|-------------|-----------|--------|--------|----------------|------------|")
    for entry in entries:
        print(
            f"| {entry['id']} | {entry['entity_type']} | {entry['entity_id']} | {entry['status']} | "
            f"{entry['source']} | {entry['snapshot_index']} | {entry['created_at']} |"
        )


def main():
    parser = argparse.ArgumentParser(description="Query SMR task registry")
    parser.add_argument("--entity-type")
    parser.add_argument("--entity-id")
    parser.add_argument("--source")
    parser.add_argument("--status")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--show-payload", action="store_true")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    if args.entity_type and args.entity_id:
        snapshot = get_entity_snapshot(conn, args.entity_type, args.entity_id, limit=args.limit)
        conn.close()
        if not snapshot:
            raise SystemExit("No registry entries found")
        print_entries(snapshot["entries"])
        if args.show_payload:
            print("")
            print("## Latest Payload")
            print("")
            print("```json")
            print(dumps_json(snapshot["latest_entry"]["payload"]))
            print("```")
        return

    entries = list_entries(
        conn,
        entity_type=args.entity_type,
        entity_id=args.entity_id,
        source=args.source,
        status=args.status,
        limit=args.limit,
    )
    conn.close()
    print_entries(entries)


if __name__ == "__main__":
    main()
