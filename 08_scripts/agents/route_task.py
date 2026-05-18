#!/usr/bin/env python3
"""Route a registry object to the best-fit SMR agent profile."""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH, get_latest_registry_entry, get_registry_entry_by_id, route_entry


def load_entry(conn, args):
    if args.entry_id:
        entry = get_registry_entry_by_id(conn, args.entry_id)
        if entry is None:
            raise SystemExit("Registry entry not found")
        return entry
    if args.entity_type and args.entity_id:
        entry = get_latest_registry_entry(conn, args.entity_type, args.entity_id)
        if entry is None:
            raise SystemExit("Registry entity not found")
        return entry
    raise SystemExit("Provide --entry-id or both --entity-type and --entity-id")


def print_route(route):
    entry = route["entry"]
    print(f"Entity: {entry['entity_type']} / {entry['entity_id']}")
    print(f"Registry Entry: {entry['id']}")
    print(f"Status: {entry['status']}")
    print(f"Source: {entry['source']}")
    print("")
    if not route["matched"]:
        print("Route: no matching profile")
        return

    print(f"Profile: {route['profile_id']}")
    print(f"Lane: {route['lane']}")
    print(f"Role: {route['role']}")
    print(f"Workspace: {route['workspace_rel_path']}")
    print(f"Match Reason: {route['match_reason']}")
    suggestion = route["suggested_handoff"]
    if not suggestion:
        print("Suggested Handoff: none")
        return
    print("")
    print("Suggested Handoff")
    print(f"- To Profile: {suggestion['to_profile_id']}")
    print(f"- Handoff Type: {suggestion['handoff_type']}")
    print(f"- Required Action: {suggestion['required_action']}")
    print(f"- Expected Outputs: {json.dumps(suggestion['expected_outputs'], ensure_ascii=False, sort_keys=True)}")


def main():
    parser = argparse.ArgumentParser(description="Route a registry object to an SMR agent profile")
    parser.add_argument("--entry-id")
    parser.add_argument("--entity-type")
    parser.add_argument("--entity-id")
    parser.add_argument("--as-json", action="store_true")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    entry = load_entry(conn, args)
    conn.close()

    route = route_entry(entry)
    if args.as_json:
        print(json.dumps(route, ensure_ascii=False, indent=2, sort_keys=True))
        return
    print_route(route)


if __name__ == "__main__":
    main()
