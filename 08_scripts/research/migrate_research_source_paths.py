#!/usr/bin/env python3
"""Normalize legacy research_index file paths onto the current project root."""

import argparse
import sqlite3
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_paths import normalize_project_path, project_path, relative_to_project
from smr_registry import register_snapshot
from smr_runlog import log_run

DB_PATH = project_path("01_data", "db", "smr.db")
REPORT_PATH = project_path("02_research", "summary", "research_source_migration_latest.md")


def classify_row(raw_path):
    normalized = normalize_project_path(raw_path)
    normalized_str = str(normalized) if normalized else None
    normalized_exists = bool(normalized and normalized.exists())
    is_legacy = str(raw_path or "").startswith("/Users/apple/")
    is_same_path = bool(raw_path and normalized_str and str(raw_path) == normalized_str)

    if not raw_path:
        status = "missing_path"
    elif not normalized:
        status = "unresolved_path"
    elif is_same_path:
        status = "already_current_exists" if normalized_exists else "already_current_missing"
    elif normalized_exists:
        status = "migratable_legacy_path" if is_legacy else "migratable_noncanonical_path"
    else:
        status = "legacy_path_missing" if is_legacy else "normalized_path_missing"

    return {
        "raw_path": raw_path,
        "normalized_path": normalized_str,
        "normalized_rel_path": relative_to_project(normalized) if normalized else None,
        "normalized_exists": normalized_exists,
        "is_legacy": is_legacy,
        "status": status,
        "can_update": status in {"migratable_legacy_path", "migratable_noncanonical_path"},
    }


def render_report(rows, counts, apply_mode, applied_count):
    lines = [
        "# Research Source Migration",
        "",
        f"- generated_at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"- apply_mode: {'apply' if apply_mode else 'dry_run'}",
        f"- total_reports: {len(rows)}",
        f"- applied_count: {applied_count}",
        "",
        "## Counts",
        "",
    ]
    for key in sorted(counts):
        lines.append(f"- `{key}`: {counts[key]}")
    lines.extend(
        [
            "",
            "## Entries",
            "",
            "| report_id | status | old_path | normalized_path | updated |",
            "|-----------|--------|----------|-----------------|---------|",
        ]
    )
    for row in rows:
        lines.append(
            "| {report_id} | {status} | {old_path} | {new_path} | {updated} |".format(
                report_id=str(row["report_id"]).replace("|", "\\|"),
                status=row["status"],
                old_path=str(row["raw_path"] or "").replace("|", "\\|"),
                new_path=str(row["normalized_rel_path"] or row["normalized_path"] or "").replace("|", "\\|"),
                updated="yes" if row["updated"] else "no",
            )
        )
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description="Normalize legacy research_index file paths")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Persist normalized paths back into research_index; default is dry-run report only",
    )
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        """
        SELECT report_id, report_type, title, created_at, file_path
        FROM research_index
        ORDER BY datetime(created_at) DESC, report_id DESC
        """
    ).fetchall()

    processed = []
    counts = Counter()
    applied_count = 0
    for report_id, report_type, title, created_at, file_path in rows:
        info = classify_row(file_path)
        counts[info["status"]] += 1
        updated = False
        if args.apply and info["can_update"]:
            conn.execute(
                "UPDATE research_index SET file_path = ? WHERE report_id = ?",
                (info["normalized_path"], report_id),
            )
            updated = conn.total_changes > applied_count
            if updated:
                applied_count += 1
        processed.append(
            {
                "report_id": report_id,
                "report_type": report_type,
                "title": title,
                "created_at": created_at,
                "updated": updated,
                **info,
            }
        )

    render_report(processed, counts, args.apply, applied_count)

    register_snapshot(
        conn,
        entity_type="research_source_migration",
        entity_id=datetime.now().strftime("%Y-%m-%d"),
        status="applied" if args.apply else "dry_run",
        source="migrate_research_source_paths.py",
        relationships={"report_rel_path": relative_to_project(REPORT_PATH)},
        payload={
            "total_reports": len(processed),
            "applied_count": applied_count,
            "counts_by_status": dict(counts),
            "updated_report_ids": [item["report_id"] for item in processed if item["updated"]],
        },
    )
    conn.commit()
    conn.close()

    log_run(
        "migrate_research_source_paths.py",
        "success",
        "research source paths normalized",
        {
            "mode": "apply" if args.apply else "dry_run",
            "total_reports": len(processed),
            "applied_count": applied_count,
            "counts_by_status": dict(counts),
            "report_path": str(REPORT_PATH),
        },
    )
    print(f"Research source migration report written: {REPORT_PATH}")
    print(f"Mode: {'apply' if args.apply else 'dry_run'}")
    print(f"Applied updates: {applied_count}")
    for key in sorted(counts):
        print(f"- {key}: {counts[key]}")


if __name__ == "__main__":
    main()
