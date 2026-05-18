#!/usr/bin/env python3
"""Apply a review-only dispatch board patch candidate to the live dispatch board safely."""

import argparse
import sqlite3
import sys
from datetime import datetime
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH, get_latest_registry_entry, get_profile, profile_workspace_path
from smr_paths import normalize_project_path, project_path, relative_to_project
from smr_registry import register_snapshot
from smr_runlog import log_run

DISPATCH_BOARD_PATH = project_path("00_control", "dispatch_board.md")


def load_patch_entry(conn, target_date):
    entry = get_latest_registry_entry(conn, "dispatch_board_patch_candidate", target_date)
    if entry is None:
        raise SystemExit(f"dispatch_board_patch_candidate not found for date: {target_date}")
    return entry


def load_preview_path(entry):
    payload = entry.get("payload", {})
    preview_rel_path = payload.get("dispatch_board_preview_rel_path")
    if not preview_rel_path:
        raise SystemExit("dispatch_board_preview_rel_path missing in patch candidate payload")
    preview_path = normalize_project_path(preview_rel_path)
    if preview_path is None or not preview_path.exists():
        raise SystemExit("dispatch board preview file missing")
    return preview_path, preview_rel_path


def main():
    parser = argparse.ArgumentParser(description="Apply dispatch board patch candidate safely")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    patch_entry = load_patch_entry(conn, args.date)
    preview_path, preview_rel_path = load_preview_path(patch_entry)
    preview_text = preview_path.read_text(encoding="utf-8")
    current_text = DISPATCH_BOARD_PATH.read_text(encoding="utf-8")

    profile = get_profile("hermes_reporting_editor")
    workspace = profile_workspace_path(profile)
    backup_dir = workspace / "dispatch_patches" / "applied_backups"
    backup_name = f"{args.date}__{datetime.now().strftime('%Y%m%d_%H%M%S')}__dispatch_board.md"
    backup_path = backup_dir / backup_name

    if args.dry_run:
        print(f"date: {args.date}")
        print(f"target_rel_path: {relative_to_project(DISPATCH_BOARD_PATH)}")
        print(f"preview_rel_path: {preview_rel_path}")
        print(f"backup_rel_path: {relative_to_project(backup_path)}")
        print(f"needs_apply: {current_text != preview_text}")
        conn.close()
        return

    backup_dir.mkdir(parents=True, exist_ok=True)
    backup_path.write_text(current_text, encoding="utf-8")

    if current_text != preview_text:
        DISPATCH_BOARD_PATH.write_text(preview_text, encoding="utf-8")
        status = "applied"
        summary = "dispatch board patch candidate applied to live dispatch board"
    else:
        status = "already_current"
        summary = "dispatch board already matched latest preview"

    apply_entry = register_snapshot(
        conn,
        entity_type="dispatch_board_apply_execution",
        entity_id=args.date,
        status=status,
        source="apply_dispatch_board_patch_candidate.py",
        relationships={
            "target_rel_path": relative_to_project(DISPATCH_BOARD_PATH),
            "preview_rel_path": preview_rel_path,
        },
        payload={
            "backup_rel_path": relative_to_project(backup_path),
            "target_rel_path": relative_to_project(DISPATCH_BOARD_PATH),
            "preview_rel_path": preview_rel_path,
            "patch_entry_id": patch_entry["id"],
        },
    )
    conn.commit()
    conn.close()

    log_run(
        "apply_dispatch_board_patch_candidate.py",
        "success",
        summary,
        {
            "date": args.date,
            "status": status,
            "backup_rel_path": relative_to_project(backup_path),
            "target_rel_path": relative_to_project(DISPATCH_BOARD_PATH),
            "preview_rel_path": preview_rel_path,
            "registry_entry_id": apply_entry["id"],
        },
    )
    print(f"Dispatch board apply execution: {status}")
    print(f"  target_rel_path={relative_to_project(DISPATCH_BOARD_PATH)}")
    print(f"  backup_rel_path={relative_to_project(backup_path)}")
    print(f"  preview_rel_path={preview_rel_path}")


if __name__ == "__main__":
    main()
