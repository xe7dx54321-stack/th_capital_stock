#!/usr/bin/env python3
"""Build a review-only dispatch board patch candidate from the latest dispatch packet."""

import argparse
import difflib
import json
import re
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH, get_latest_registry_entry, get_profile, profile_workspace_path
from smr_paths import normalize_project_path, project_path, relative_to_project
from smr_registry import register_snapshot
from smr_runlog import log_run

DISPATCH_BOARD_PATH = project_path("00_control", "dispatch_board.md")


def load_packet_entry(conn, target_date):
    entry = get_latest_registry_entry(conn, "dispatch_packet_candidate", target_date)
    if entry is None:
        raise SystemExit(f"dispatch_packet_candidate not found for date: {target_date}")
    return entry


def load_payload(entry):
    return entry.get("payload", {}) if isinstance(entry, dict) else {}


def read_rel_path_text(rel_path):
    if not rel_path:
        return ""
    path = normalize_project_path(rel_path)
    if path is None or not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def extract_candidate_index(packet_text):
    items = []
    in_index = False
    for raw_line in packet_text.splitlines():
        line = raw_line.strip()
        if line == "## 候选块索引":
            in_index = True
            continue
        if not in_index:
            continue
        if line.startswith("## "):
            break
        if not line.startswith("- `"):
            continue
        match = re.match(r"- `([^`]+)` / `([^`]+)` -> `([^`]*)`", line)
        if not match:
            continue
        items.append(
            {
                "entity_type": match.group(1),
                "entity_id": match.group(2),
                "rel_path": match.group(3),
            }
        )
    return items


def sort_candidate_items(items):
    def score(item):
        entity_id = item["entity_id"]
        entity_type = item["entity_type"]
        if entity_type == "dispatch_update_candidate":
            return (0, entity_id)
        if "dynamic_pool_snapshot" in entity_id:
            return (1, entity_id)
        if "trend_research_batch" in entity_id:
            return (2, entity_id)
        if "research_quality_snapshot" in entity_id:
            return (3, entity_id)
        if "us_signal_snapshot" in entity_id:
            return (4, entity_id)
        if "stock_objective_monitor_snapshot" in entity_id:
            return (5, entity_id)
        if "strategy_watch_batch" in entity_id:
            return (6, entity_id)
        if "rotation_candidate_snapshot" in entity_id:
            return (7, entity_id)
        if "rotation_execution_plan_snapshot" in entity_id:
            return (8, entity_id)
        if "risk_monitor_snapshot" in entity_id:
            return (9, entity_id)
        if "portfolio_pnl_snapshot" in entity_id:
            return (10, entity_id)
        return (11, entity_id)

    return sorted(items, key=score)


def extract_primary_block(text):
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.startswith("### "):
            start = index
            break
    if start is None:
        return []
    block = []
    for index in range(start, len(lines)):
        line = lines[index]
        if index > start and line.startswith("### "):
            break
        block.append(line)
    while block and block[-1] == "":
        block.pop()
    return block


def build_sync_section(target_date, packet_rel_path, items):
    lines = [
        f"## 自动同步候选（{target_date}）",
        "",
        f"- source_dispatch_packet_rel_path: `{packet_rel_path or ''}`",
        "- apply_mode: `review_only`",
        "- 说明：这是一份自动生成的写回候选，只补充新说明，不直接覆盖旧口径。",
        "",
    ]
    for item in sort_candidate_items(items):
        text = read_rel_path_text(item["rel_path"])
        block = extract_primary_block(text)
        if not block:
            continue
        lines.extend(block)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def replace_or_insert_section(board_text, target_date, new_section_text):
    heading = f"## 自动同步候选（{target_date}）"
    if heading in board_text:
        start = board_text.index(heading)
        anchor = board_text.find("\n## 备注", start + len(heading))
        if anchor == -1:
            return board_text[:start].rstrip() + "\n\n" + new_section_text
        return board_text[:start].rstrip() + "\n\n" + new_section_text + "\n" + board_text[anchor + 1 :].lstrip()

    anchor = "\n## 备注"
    if anchor in board_text:
        index = board_text.index(anchor)
        return board_text[:index].rstrip() + "\n\n" + new_section_text + "\n" + board_text[index + 1 :].lstrip()
    return board_text.rstrip() + "\n\n" + new_section_text


def update_header_dates(board_text, generated_at, next_update):
    updated = re.sub(
        r"^\*\*更新日期\*\*：.*$",
        f"**更新日期**：{generated_at}",
        board_text,
        flags=re.MULTILINE,
    )
    updated = re.sub(
        r"^\*\*下次更新\*\*：.*$",
        f"**下次更新**：{next_update}",
        updated,
        flags=re.MULTILINE,
    )
    updated = re.sub(
        r"^\*📝 SMR 调度面板.*\*$",
        f"*📝 SMR 调度面板 | 同行资本二级市场研究 | {generated_at}*",
        updated,
        flags=re.MULTILINE,
    )
    return updated


def build_patch_markdown(target_rel_path, packet_rel_path, preview_rel_path, section_text, diff_text, generated_at):
    lines = [
        f"# 调度板写回候选：{generated_at[:10]}",
        "",
        f"- target_rel_path: `{target_rel_path}`",
        f"- source_dispatch_packet_rel_path: `{packet_rel_path or ''}`",
        f"- preview_rel_path: `{preview_rel_path}`",
        "- apply_mode: `review_only`",
        f"- generated_at: `{generated_at}`",
        "",
        "## 建议新增块",
        "",
        section_text.rstrip(),
        "",
        "## Unified Diff（统一差异）",
        "",
        "```diff",
        diff_text.rstrip(),
        "```",
        "",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Build review-only dispatch board patch candidate")
    parser.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    packet_entry = load_packet_entry(conn, args.date)
    packet_payload = load_payload(packet_entry)
    packet_rel_path = packet_payload.get("dispatch_packet_rel_path")
    packet_text = read_rel_path_text(packet_rel_path)
    if not packet_text:
        conn.close()
        raise SystemExit("dispatch packet candidate file missing or empty")

    profile = get_profile("hermes_reporting_editor")
    workspace = profile_workspace_path(profile)
    patch_dir = workspace / "dispatch_patches"
    patch_path = patch_dir / f"{args.date}__dispatch_board_patch_candidate.md"
    preview_path = patch_dir / f"{args.date}__dispatch_board_preview.md"

    items = extract_candidate_index(packet_text)
    if args.dry_run:
        print(f"date: {args.date}")
        print(f"packet_rel_path: {packet_rel_path}")
        print(f"candidate_item_count: {len(items)}")
        print(f"patch_rel_path: {relative_to_project(patch_path)}")
        print(f"preview_rel_path: {relative_to_project(preview_path)}")
        conn.close()
        return

    patch_dir.mkdir(parents=True, exist_ok=True)
    generated_dt = datetime.now()
    generated_at = generated_dt.strftime("%Y-%m-%d %H:%M:%S CST")
    next_update = (generated_dt + timedelta(days=1)).strftime("%Y-%m-%d 22:00 CST")

    board_text = DISPATCH_BOARD_PATH.read_text(encoding="utf-8")
    section_text = build_sync_section(args.date, packet_rel_path, items)
    preview_text = replace_or_insert_section(board_text, args.date, section_text)
    preview_text = update_header_dates(preview_text, generated_at, next_update)

    diff_lines = difflib.unified_diff(
        board_text.splitlines(keepends=True),
        preview_text.splitlines(keepends=True),
        fromfile=f"a/{relative_to_project(DISPATCH_BOARD_PATH)}",
        tofile=f"b/{relative_to_project(DISPATCH_BOARD_PATH)}",
    )
    diff_text = "".join(diff_lines)

    preview_path.write_text(preview_text, encoding="utf-8")
    patch_path.write_text(
        build_patch_markdown(
            relative_to_project(DISPATCH_BOARD_PATH),
            packet_rel_path,
            relative_to_project(preview_path),
            section_text,
            diff_text,
            generated_at,
        ),
        encoding="utf-8",
    )

    patch_entry = register_snapshot(
        conn,
        entity_type="dispatch_board_patch_candidate",
        entity_id=args.date,
        status="created",
        source="build_dispatch_board_patch_candidate.py",
        relationships={
            "target_rel_path": relative_to_project(DISPATCH_BOARD_PATH),
        },
        payload={
            "dispatch_board_patch_rel_path": relative_to_project(patch_path),
            "dispatch_board_preview_rel_path": relative_to_project(preview_path),
            "dispatch_packet_rel_path": packet_rel_path,
            "candidate_item_count": len(items),
        },
    )
    conn.commit()
    conn.close()

    log_run(
        "build_dispatch_board_patch_candidate.py",
        "success",
        "dispatch board patch candidate built",
        {
            "date": args.date,
            "dispatch_board_patch_rel_path": relative_to_project(patch_path),
            "dispatch_board_preview_rel_path": relative_to_project(preview_path),
            "candidate_item_count": len(items),
            "registry_entry_id": patch_entry["id"],
        },
    )
    print(f"Dispatch board patch candidate: {patch_path}")
    print(f"  preview_rel_path={relative_to_project(preview_path)}")
    print(f"  candidate_item_count={len(items)}")


if __name__ == "__main__":
    main()
