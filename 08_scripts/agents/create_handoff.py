#!/usr/bin/env python3
"""Create an SMR agent handoff from a registry object."""

import argparse
import json
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import (
    DB_PATH,
    create_handoff,
    default_expected_outputs,
    default_handoff_type,
    default_inputs_from_entry,
    default_required_action,
    get_latest_registry_entry,
    get_registry_entry_by_id,
    route_entry,
)
from smr_runlog import log_run


def parse_json_arg(value, fallback):
    if value in (None, ""):
        return fallback
    return json.loads(value)


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


def main():
    parser = argparse.ArgumentParser(description="Create an SMR agent handoff")
    parser.add_argument("--entry-id")
    parser.add_argument("--entity-type")
    parser.add_argument("--entity-id")
    parser.add_argument("--from-profile")
    parser.add_argument("--to-profile")
    parser.add_argument("--handoff-type")
    parser.add_argument("--required-action")
    parser.add_argument("--inputs-json")
    parser.add_argument("--expected-json")
    parser.add_argument("--note")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    entry = load_entry(conn, args)
    route = route_entry(entry)
    if not route["matched"] and not args.from_profile:
        conn.close()
        raise SystemExit("No matching source profile found; pass --from-profile explicitly")

    from_profile_id = args.from_profile or route["profile_id"]
    suggested = route.get("suggested_handoff") or {}
    to_profile_id = args.to_profile or suggested.get("to_profile_id")
    if not to_profile_id:
        conn.close()
        raise SystemExit("No target profile provided and no suggested handoff available")

    handoff_type = args.handoff_type or suggested.get("handoff_type") or default_handoff_type(entry, to_profile_id)
    required_action = (
        args.required_action or suggested.get("required_action") or default_required_action(entry, to_profile_id)
    )
    inputs = parse_json_arg(args.inputs_json, default_inputs_from_entry(entry))
    expected_outputs = parse_json_arg(
        args.expected_json,
        suggested.get("expected_outputs") or default_expected_outputs(entry, to_profile_id),
    )

    record = create_handoff(
        conn,
        from_profile_id=from_profile_id,
        to_profile_id=to_profile_id,
        handoff_type=handoff_type,
        entity_type=entry["entity_type"],
        entity_id=entry["entity_id"],
        required_action=required_action,
        source_entry_id=entry["id"],
        inputs=inputs,
        expected_outputs=expected_outputs,
        note=args.note,
    )
    conn.commit()
    conn.close()

    log_run(
        "create_handoff.py",
        "success",
        "agent handoff created",
        {
            "handoff_id": record["handoff_id"],
            "from_profile_id": from_profile_id,
            "to_profile_id": to_profile_id,
            "entity_type": entry["entity_type"],
            "entity_id": entry["entity_id"],
        },
    )
    print(f"Created handoff: {record['handoff_id']}")
    print(f"Path: {record['handoff_rel_path']}")
    print(f"Route: {from_profile_id} -> {to_profile_id}")


if __name__ == "__main__":
    main()
