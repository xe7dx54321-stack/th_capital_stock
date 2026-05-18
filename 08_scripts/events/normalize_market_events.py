#!/usr/bin/env python3
"""Normalize existing raw external sources into first-pass market_event rows."""

import argparse
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_events import (
    EVENT_OUTPUT_DIR,
    count_by_key,
    delete_stale_market_events,
    ensure_market_event_table,
    event_rows_from_raw_external,
    load_source_manifest_lookup,
    upsert_market_events,
)
from smr_paths import project_path, relative_to_project
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import loads_json, now_ts

DB_PATH = project_path("01_data", "db", "smr.db")


def write_snapshot(path, created_at, rows, stale_deleted_count=0):
    counts_by_family = count_by_key(rows, "event_family")
    counts_by_type = count_by_key(rows, "event_type")
    high_rows = [row for row in rows if row.get("importance") == "high"][:15]
    lines = [
        "# SMR 市场事件快照",
        "",
        f"- created_at: {created_at}",
        f"- event_count: {len(rows)}",
        f"- stale_deleted_count: {stale_deleted_count}",
        f"- counts_by_family: {counts_by_family}",
        f"- counts_by_type: {counts_by_type}",
        "",
        "## High Importance Events",
        "",
    ]
    if not high_rows:
        lines.append("- 当前筛选窗口内没有 high 级事件。")
        lines.append("")
    else:
        for row in high_rows:
            payload = loads_json(row["payload_json"], {}) if isinstance(row["payload_json"], str) else {}
            lines.extend(
                [
                    f"### {row['title']}",
                    "",
                    f"- entity: `{row['entity_id']}`",
                    f"- family/type: `{row['event_family']}` / `{row['event_type']}`",
                    f"- event_date: `{row.get('event_date') or '-'}`",
                    f"- publish_time: `{row.get('publish_time') or '-'}`",
                    f"- market_effective_time: `{row.get('market_effective_time') or '-'}`",
                    f"- source_key: `{row['source_key']}`",
                    f"- source_rel_path: `{row.get('source_rel_path') or '-'}`",
                    f"- summary: {payload.get('summary') or '-'}",
                    "",
                ]
            )

    lines.extend(
        [
            "## Recent Events",
            "",
            "| Event Date | Entity | Family | Type | Importance | Title |",
            "|------------|--------|--------|------|------------|-------|",
        ]
    )
    for row in rows[:40]:
        lines.append(
            "| {event_date} | {entity_id} | {event_family} | {event_type} | {importance} | {title} |".format(
                event_date=row.get("event_date") or "-",
                entity_id=row["entity_id"],
                event_family=row["event_family"],
                event_type=row["event_type"],
                importance=row["importance"],
                title=row["title"].replace("|", "/"),
            )
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Normalize raw external sources into first-pass market events")
    parser.add_argument("--days-back", type=int, default=60, help="Only include events on/after today-N days")
    parser.add_argument("--limit", type=int, help="Maximum number of raw files to normalize")
    parser.add_argument(
        "--family",
        action="append",
        choices=["announcement", "research", "news", "calendar", "capital_flow", "macro", "risk"],
        help="Restrict to selected event family; can be repeated",
    )
    args = parser.parse_args()

    created_at = now_ts()
    snapshot_date = created_at[:10]
    EVENT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = EVENT_OUTPUT_DIR / f"{snapshot_date}_market_event_snapshot.md"

    conn = sqlite3.connect(DB_PATH)
    ensure_market_event_table(conn)
    source_lookup = load_source_manifest_lookup(conn)
    rows = event_rows_from_raw_external(
        source_lookup,
        days_back=args.days_back,
        limit=args.limit,
        families=set(args.family or []),
    )
    if not rows:
        raise SystemExit("No raw external sources matched the requested filters")
    upsert_market_events(conn, rows)
    stale_deleted_count = delete_stale_market_events(conn, rows)
    write_snapshot(output_path, created_at, rows, stale_deleted_count=stale_deleted_count)
    entry = register_snapshot(
        conn,
        entity_type="market_event_snapshot",
        entity_id=snapshot_date,
        status="normalized",
        source="normalize_market_events.py",
        relationships={
            "summary_rel_path": relative_to_project(output_path),
        },
        payload={
            "event_count": len(rows),
            "stale_deleted_count": stale_deleted_count,
            "counts_by_family": count_by_key(rows, "event_family"),
            "counts_by_type": count_by_key(rows, "event_type"),
            "summary_rel_path": relative_to_project(output_path),
        },
    )
    conn.commit()
    conn.close()

    log_run(
        "normalize_market_events.py",
        "success",
        "market events normalized from raw external sources",
        {
            "entity_id": snapshot_date,
            "event_count": len(rows),
            "stale_deleted_count": stale_deleted_count,
            "counts_by_family": count_by_key(rows, "event_family"),
            "summary_rel_path": relative_to_project(output_path),
            "registry_entry_id": entry["id"],
        },
    )
    print(f"Market event snapshot registered: {snapshot_date}")
    print(f"Summary file: {output_path}")
    print(f"Event count: {len(rows)}")


if __name__ == "__main__":
    main()
