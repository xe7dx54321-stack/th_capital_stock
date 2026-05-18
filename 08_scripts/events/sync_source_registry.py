#!/usr/bin/env python3
"""Sync 00_control/source_registry.md into SQLite and write a snapshot summary."""

import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_events import EVENT_OUTPUT_DIR, parse_source_registry, upsert_input_source_registry
from smr_paths import project_path, relative_to_project
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts

DB_PATH = project_path("01_data", "db", "smr.db")


def write_snapshot(path, created_at, rows):
    counts_by_status = {}
    counts_by_layer = {}
    for row in rows:
        counts_by_status[row["status"]] = counts_by_status.get(row["status"], 0) + 1
        counts_by_layer[row["layer"]] = counts_by_layer.get(row["layer"], 0) + 1

    lines = [
        "# SMR 输入源注册表快照",
        "",
        f"- created_at: {created_at}",
        f"- source_count: {len(rows)}",
        f"- counts_by_status: {counts_by_status}",
        f"- counts_by_layer: {counts_by_layer}",
        "",
        "## Sources",
        "",
        "| Source Key | Layer | Provider | Status | Enabled | Cadence | Owner |",
        "|------------|-------|----------|--------|---------|---------|-------|",
    ]
    for row in rows:
        lines.append(
            "| {source_key} | {layer} | {provider} | {status} | {enabled} | {cadence} | {owner_profile_id} |".format(
                source_key=row["source_key"],
                layer=row["layer"],
                provider=row["provider"],
                status=row["status"],
                enabled="yes" if row["enabled"] else "no",
                cadence=row["cadence"],
                owner_profile_id=row["owner_profile_id"] or "-",
            )
        )
    path.write_text("\n".join(lines), encoding="utf-8")


def main():
    rows = parse_source_registry()
    if not rows:
        raise SystemExit("No source registry rows parsed from 00_control/source_registry.md")

    created_at = now_ts()
    snapshot_date = created_at[:10]
    counts_by_status = {key: sum(1 for row in rows if row["status"] == key) for key in sorted({row["status"] for row in rows})}
    counts_by_layer = {key: sum(1 for row in rows if row["layer"] == key) for key in sorted({row["layer"] for row in rows})}
    EVENT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = EVENT_OUTPUT_DIR / f"{snapshot_date}_source_registry_snapshot.md"

    conn = sqlite3.connect(DB_PATH)
    upsert_input_source_registry(conn, rows)
    write_snapshot(output_path, created_at, rows)
    entry = register_snapshot(
        conn,
        entity_type="input_source_registry_snapshot",
        entity_id=snapshot_date,
        status="synced",
        source="sync_source_registry.py",
        relationships={
            "summary_rel_path": relative_to_project(output_path),
        },
        payload={
            "source_count": len(rows),
            "counts_by_status": counts_by_status,
            "counts_by_layer": counts_by_layer,
            "summary_rel_path": relative_to_project(output_path),
        },
    )
    conn.commit()
    conn.close()

    log_run(
        "sync_source_registry.py",
        "success",
        "input source registry synced",
        {
            "entity_id": snapshot_date,
            "source_count": len(rows),
            "summary_rel_path": relative_to_project(output_path),
            "registry_entry_id": entry["id"],
        },
    )
    print(f"Input source registry snapshot registered: {snapshot_date}")
    print(f"Summary file: {output_path}")
    print(f"Source count: {len(rows)}")


if __name__ == "__main__":
    main()
