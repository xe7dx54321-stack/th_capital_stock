#!/usr/bin/env python3
"""Build a daily dispatch packet candidate from reporting/research/risk candidates."""

import argparse
import json
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH, get_profile, get_registry_entry_by_id, profile_workspace_path
from smr_paths import normalize_project_path, relative_to_project
from smr_registry import ensure_task_registry_tables, register_snapshot
from smr_runlog import log_run

DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")


def parse_payload(entry):
    try:
        return json.loads(entry["payload_json"] or "{}")
    except json.JSONDecodeError:
        return {}


def parse_relationships(entry):
    try:
        return json.loads(entry["relationships_json"] or "{}")
    except json.JSONDecodeError:
        return {}


def matches_target_date(entry, entity_type, target_date):
    payload = parse_payload(entry)
    dispatch_date = payload.get("dispatch_date")
    if dispatch_date:
        return dispatch_date == target_date
    entity_id = entry["entity_id"]
    if entity_type == "dispatch_update_candidate":
        return entity_id.startswith(target_date)
    return target_date in entity_id


def load_entries_for_date(conn, entity_type, target_date, limit=20, scan_limit=200):
    ensure_task_registry_tables(conn)
    rows = conn.execute(
        """
        SELECT
            id,
            entity_type,
            entity_id,
            status,
            source,
            relationships_json,
            payload_json,
            snapshot_index,
            created_at
        FROM task_registry_entity_latest
        WHERE entity_type=?
        ORDER BY datetime(created_at) DESC, snapshot_index DESC, id DESC
        LIMIT ?
        """,
        (entity_type, scan_limit),
    ).fetchall()
    results = []
    for row in rows:
        entry = {
            "id": row[0],
            "entity_type": row[1],
            "entity_id": row[2],
            "status": row[3],
            "source": row[4],
            "relationships_json": row[5] or "{}",
            "payload_json": row[6] or "{}",
            "snapshot_index": row[7],
            "created_at": row[8],
        }
        if not matches_target_date(entry, entity_type, target_date):
            continue
        results.append(entry)
        if len(results) >= limit:
            break
    return results


def parse_datetime(value):
    if not value:
        return datetime.min
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return datetime.min


def parse_date(value):
    if not value:
        return datetime.min.date()
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except ValueError:
        return datetime.min.date()


def extract_date(value):
    if not value:
        return ""
    match = DATE_RE.search(str(value))
    return match.group(0) if match else ""


def latest_entry_key(entry):
    return (
        parse_datetime(entry.get("created_at")),
        int(entry.get("snapshot_index") or 0),
        str(entry.get("id") or ""),
    )


def dedupe_dispatch_updates(entries):
    latest_by_key = {}
    for entry in entries:
        relationships = parse_relationships(entry)
        payload = parse_payload(entry)
        dedupe_key = (
            relationships.get("daily_reporting_snapshot_id")
            or payload.get("dispatch_date")
            or entry["entity_id"]
        )
        current = latest_by_key.get(dedupe_key)
        if current is None or latest_entry_key(entry) > latest_entry_key(current):
            latest_by_key[dedupe_key] = entry
    return sorted(latest_by_key.values(), key=latest_entry_key, reverse=True)


def resolve_dispatch_sync_lineage(conn, entry):
    cached = entry.get("_dispatch_sync_lineage")
    if cached is not None:
        return cached

    relationships = parse_relationships(entry)
    payload = parse_payload(entry)
    source_entry_id = payload.get("source_entry_id")
    source_entry = get_registry_entry_by_id(conn, source_entry_id) if source_entry_id else None
    source_relationships = source_entry.get("relationships", {}) if source_entry else {}

    source_entity_ref = relationships.get("source_entity_id") or entry["entity_id"]
    upstream_entity_type = source_relationships.get("source_entity_type")
    if not upstream_entity_type and source_entity_ref:
        upstream_entity_type = str(source_entity_ref).split("__", 1)[0]

    upstream_entity_id = source_relationships.get("source_entity_id") or extract_date(source_entity_ref)
    if not upstream_entity_id:
        upstream_entity_id = extract_date(entry["entity_id"])

    lineage = {
        "handoff_entity_type": relationships.get("source_entity_type") or entry["entity_type"],
        "handoff_entity_id": source_entity_ref,
        "note_entity_type": source_entry.get("entity_type") if source_entry else "",
        "note_entity_id": source_entry.get("entity_id") if source_entry else "",
        "upstream_entity_type": upstream_entity_type or "",
        "upstream_entity_id": upstream_entity_id or "",
        "upstream_business_date": extract_date(upstream_entity_id)
        or extract_date(source_entity_ref)
        or extract_date(entry["entity_id"]),
        "note_created_at": source_entry.get("created_at") if source_entry else "",
    }
    entry["_dispatch_sync_lineage"] = lineage
    return lineage


def dispatch_sync_group_key(conn, entry):
    lineage = resolve_dispatch_sync_lineage(conn, entry)
    return (
        lineage.get("handoff_entity_type") or entry["entity_type"],
        lineage.get("upstream_entity_type") or lineage.get("note_entity_type") or entry["entity_id"],
    )


def dispatch_sync_priority_key(conn, entry):
    lineage = resolve_dispatch_sync_lineage(conn, entry)
    return (
        parse_date(lineage.get("upstream_business_date")),
        parse_datetime(lineage.get("note_created_at")),
        parse_datetime(entry.get("created_at")),
        int(entry.get("snapshot_index") or 0),
        str(entry.get("id") or ""),
    )


def dedupe_dispatch_syncs(conn, entries):
    latest_by_key = {}
    for entry in entries:
        dedupe_key = dispatch_sync_group_key(conn, entry)
        current = latest_by_key.get(dedupe_key)
        if current is None or dispatch_sync_priority_key(conn, entry) > dispatch_sync_priority_key(conn, current):
            latest_by_key[dedupe_key] = entry
    return sorted(latest_by_key.values(), key=lambda entry: dispatch_sync_priority_key(conn, entry), reverse=True)


def read_rel_path_text(rel_path):
    if not rel_path:
        return ""
    path = normalize_project_path(rel_path)
    if path is None or not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def payload_rel_path(entry):
    payload = parse_payload(entry)
    return payload.get("dispatch_candidate_rel_path") or payload.get("dispatch_sync_rel_path")


def render_entry_block(entry, rel_path):
    text = read_rel_path_text(rel_path)
    lines = [
        f"### {entry['entity_type']} / {entry['entity_id']}",
        "",
        f"- registry_entry_id: `{entry['id']}`",
        f"- created_at: `{entry['created_at']}`",
        f"- rel_path: `{rel_path or ''}`",
        "",
    ]
    if text:
        body = text.strip().splitlines()
        if body and body[0].startswith("# "):
            body = body[1:]
        lines.extend(body)
        lines.append("")
    else:
        lines.append("- 当前候选文件不存在或为空。")
        lines.append("")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Build dispatch packet candidate")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    dispatch_entries = load_entries_for_date(conn, "dispatch_update_candidate", args.date, limit=10)
    dispatch_entries = dedupe_dispatch_updates(dispatch_entries)
    sync_entries = load_entries_for_date(conn, "dispatch_sync_candidate", args.date, limit=20)
    sync_entries = dedupe_dispatch_syncs(conn, sync_entries)

    profile = get_profile("hermes_reporting_editor")
    workspace = profile_workspace_path(profile)
    packet_dir = workspace / "dispatch_packets"
    packet_path = packet_dir / f"{args.date}__dispatch_packet_candidate.md"

    if args.dry_run:
        print(f"date: {args.date}")
        print(f"dispatch_update_candidate_count: {len(dispatch_entries)}")
        print(f"dispatch_sync_candidate_count: {len(sync_entries)}")
        print(f"packet_rel_path: {relative_to_project(packet_path)}")
        conn.close()
        return

    packet_dir.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# 调度包候选：{args.date}",
        "",
        f"- generated_at: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`",
        f"- dispatch_update_candidate_count: `{len(dispatch_entries)}`",
        f"- dispatch_sync_candidate_count: `{len(sync_entries)}`",
        "",
        "## 候选块索引",
        "",
    ]

    for entry in dispatch_entries + sync_entries:
        rel_path = payload_rel_path(entry)
        lines.append(f"- `{entry['entity_type']}` / `{entry['entity_id']}` -> `{rel_path or ''}`")

    lines.extend(["", "## 合并视图", ""])
    for entry in dispatch_entries + sync_entries:
        rel_path = payload_rel_path(entry)
        lines.append(render_entry_block(entry, rel_path))

    packet_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    packet_entry = register_snapshot(
        conn,
        entity_type="dispatch_packet_candidate",
        entity_id=args.date,
        status="created",
        source="build_dispatch_packet_candidate.py",
        relationships={},
        payload={
            "dispatch_packet_rel_path": relative_to_project(packet_path),
            "dispatch_update_candidate_count": len(dispatch_entries),
            "dispatch_sync_candidate_count": len(sync_entries),
            "dispatch_update_candidate_ids": [entry["entity_id"] for entry in dispatch_entries],
            "dispatch_sync_candidate_ids": [entry["entity_id"] for entry in sync_entries],
        },
    )
    conn.commit()
    conn.close()

    log_run(
        "build_dispatch_packet_candidate.py",
        "success",
        "dispatch packet candidate built",
        {
            "date": args.date,
            "dispatch_packet_rel_path": relative_to_project(packet_path),
            "dispatch_update_candidate_count": len(dispatch_entries),
            "dispatch_sync_candidate_count": len(sync_entries),
            "registry_entry_id": packet_entry["id"],
        },
    )
    print(f"Dispatch packet candidate: {packet_path}")
    print(f"  dispatch_update_candidate_count={len(dispatch_entries)}")
    print(f"  dispatch_sync_candidate_count={len(sync_entries)}")


if __name__ == "__main__":
    main()
