#!/usr/bin/env python3
"""List SMR agent handoffs."""

import argparse
import json
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import list_handoffs


def print_table(records):
    print("| handoff_id | status | from_profile | to_profile | entity_type | entity_id | updated_at |")
    print("|------------|--------|--------------|------------|-------------|-----------|------------|")
    for record in records:
        print(
            f"| {record['handoff_id']} | {record['status']} | {record['from_profile_id']} | "
            f"{record['to_profile_id']} | {record['entity_type']} | {record['entity_id']} | {record['updated_at']} |"
        )


def main():
    parser = argparse.ArgumentParser(description="List SMR agent handoffs")
    parser.add_argument("--status")
    parser.add_argument("--from-profile")
    parser.add_argument("--to-profile")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--as-json", action="store_true")
    args = parser.parse_args()

    records = list_handoffs(
        status=args.status,
        from_profile_id=args.from_profile,
        to_profile_id=args.to_profile,
        limit=args.limit,
    )
    if args.as_json:
        print(json.dumps(records, ensure_ascii=False, indent=2, sort_keys=True))
        return
    print_table(records)


if __name__ == "__main__":
    main()
