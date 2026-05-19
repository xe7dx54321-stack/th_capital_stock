#!/usr/bin/env python3
"""Run the SMR agent control loop over pending handoffs and dispatch outputs."""

import argparse
import sqlite3
import subprocess
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH, get_latest_registry_entry, get_registry_entry_by_id, list_handoffs, resolve_handoff
from smr_runlog import log_run

SCRIPT_DIR = Path(__file__).resolve().parent

RESEARCH_CONTEXT_ENTITY_TYPES = {
    "dynamic_pool_snapshot",
    "opportunity_radar_snapshot",
    "opportunity_lifecycle_snapshot",
    "paper_trade_watchlist_snapshot",
    "paper_watch_performance_snapshot",
    "portfolio_action_memo_snapshot",
    "trend_research_batch",
    "research_quality_snapshot",
    "rotation_candidate_snapshot",
    "rotation_execution_plan_snapshot",
    "strategy_evidence_snapshot",
    "stock_objective_monitor_snapshot",
    "strategy_watch_batch",
    "thesis_attack_defense_snapshot",
    "us_signal_snapshot",
}
RISK_ENTITY_TYPES = {
    "portfolio_pnl_snapshot",
    "risk_monitor_snapshot",
}
REPORTING_SYNC_ENTITY_TYPES = {
    "research_context_note",
    "risk_update_candidate",
}
RESEARCH_GOVERNANCE_ENTITY_TYPES = {
    "review_queue",
    "wiki_draft",
}


def choose_command(record, research_governance_mode):
    handoff_id = record["handoff_id"]
    to_profile_id = record["to_profile_id"]
    entity_type = record["entity_type"]
    handoff_status = record["status"]

    if to_profile_id == "openclaw_system_exec" and entity_type == "system_change_request":
        command = [
            sys.executable,
            str(SCRIPT_DIR / "process_system_handoff.py"),
            "--handoff-id",
            handoff_id,
        ]
        command.append("--complete")
        return command

    if to_profile_id == "hermes_reporting_editor":
        if entity_type in {"daily_reporting_snapshot", "daily_report_candidate"}:
            command = [
                sys.executable,
                str(SCRIPT_DIR / "process_reporting_handoff.py"),
                "--handoff-id",
                handoff_id,
                "--refresh-draft",
            ]
            command.append("--complete")
            return command
        if entity_type in REPORTING_SYNC_ENTITY_TYPES:
            command = [
                sys.executable,
                str(SCRIPT_DIR / "process_reporting_sync_handoff.py"),
                "--handoff-id",
                handoff_id,
            ]
            command.append("--complete")
            return command

    if to_profile_id == "hermes_research_curator":
        if entity_type in RESEARCH_CONTEXT_ENTITY_TYPES:
            command = [
                sys.executable,
                str(SCRIPT_DIR / "process_research_context_handoff.py"),
                "--handoff-id",
                handoff_id,
            ]
            command.append("--complete")
            return command
        if entity_type in RESEARCH_GOVERNANCE_ENTITY_TYPES:
            if handoff_status != "pending":
                return None
            if research_governance_mode == "skip":
                return None
            if research_governance_mode == "accept-only":
                return [
                    sys.executable,
                    str(SCRIPT_DIR / "process_research_handoff.py"),
                    "--handoff-id",
                    handoff_id,
                    "--accept-only",
                ]
            if research_governance_mode == "dry-run":
                return [
                    sys.executable,
                    str(SCRIPT_DIR / "process_research_handoff.py"),
                    "--handoff-id",
                    handoff_id,
                    "--dry-run",
                ]

    if to_profile_id == "hermes_risk_curator" and entity_type in RISK_ENTITY_TYPES:
        command = [
            sys.executable,
            str(SCRIPT_DIR / "process_risk_handoff.py"),
            "--handoff-id",
            handoff_id,
        ]
        command.append("--complete")
        return command

    return None


def format_command(command):
    return " ".join(command)


def run_command(command, dry_run):
    if dry_run:
        return 0, "(dry-run)"
    completed = subprocess.run(command, capture_output=True, text=True)
    output = (completed.stdout or "") + (completed.stderr or "")
    return completed.returncode, output.strip()


def orphaned_source_reason(record):
    conn = sqlite3.connect(DB_PATH)
    try:
        source_entry_id = record.get("source_entry_id")
        if source_entry_id:
            entry = get_registry_entry_by_id(conn, source_entry_id)
            if entry:
                return None
        latest_entry = get_latest_registry_entry(conn, record["entity_type"], record["entity_id"])
        if latest_entry is not None:
            return None
        return (
            "source registry entry missing"
            f" (source_entry_id={record.get('source_entry_id') or ''}, "
            f"entity_type={record['entity_type']}, entity_id={record['entity_id']})"
        )
    finally:
        conn.close()


def cancel_orphaned_handoff(record, reason, dry_run):
    summary = f"自动取消孤儿 handoff：{reason}"
    if dry_run:
        return {"status": "cancelled_dry_run", "summary": summary}

    conn = sqlite3.connect(DB_PATH)
    try:
        resolved = resolve_handoff(
            conn,
            handoff_id=record["handoff_id"],
            status="cancelled",
            resolved_by="run_agent_control_loop.py",
            summary=summary,
            outputs=record.get("outputs"),
            source="run_agent_control_loop.py",
        )
        conn.commit()
        return {"status": resolved["status"], "summary": summary}
    finally:
        conn.close()


def active_handoffs(limit=500):
    records = list_handoffs(limit=limit)
    active = [record for record in records if record.get("status") in {"pending", "accepted"}]
    return sorted(active, key=lambda record: (record.get("updated_at", ""), record["handoff_id"]))


def main():
    parser = argparse.ArgumentParser(description="Run SMR agent control loop")
    parser.add_argument("--date", help="Date for dispatch outputs; defaults to today")
    parser.add_argument("--max-passes", type=int, default=5)
    parser.add_argument(
        "--research-governance-mode",
        choices=["accept-only", "dry-run", "skip"],
        default="accept-only",
        help="How to handle pending review_queue/wiki_draft handoffs",
    )
    parser.add_argument("--build-dispatch", action="store_true", help="Build dispatch packet and patch candidates")
    parser.add_argument("--apply-dispatch", action="store_true", help="Apply latest dispatch board patch candidate")
    parser.add_argument("--refresh-source-manifest", action="store_true", help="Refresh source manifest at the end")
    parser.add_argument("--continue-on-error", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    processed = []
    skipped = []
    failed = []
    seen = set()

    for pass_index in range(1, args.max_passes + 1):
        records = active_handoffs()
        todo = [record for record in records if record["handoff_id"] not in seen]
        if not todo:
            break
        print(f"Pass {pass_index}: active_handoffs={len(todo)}")
        for record in todo:
            seen.add(record["handoff_id"])
            command = choose_command(record, args.research_governance_mode)
            if command is None:
                skipped.append(
                    {
                        "handoff_id": record["handoff_id"],
                        "entity_type": record["entity_type"],
                        "to_profile_id": record["to_profile_id"],
                        "reason": "no_safe_handler",
                    }
                )
                print(
                    f"  skipped {record['handoff_id']} "
                    f"({record['entity_type']} -> {record['to_profile_id']}): no_safe_handler"
                )
                continue

            orphan_reason = orphaned_source_reason(record)
            if orphan_reason:
                cancel_result = cancel_orphaned_handoff(record, orphan_reason, args.dry_run)
                skipped.append(
                    {
                        "handoff_id": record["handoff_id"],
                        "entity_type": record["entity_type"],
                        "to_profile_id": record["to_profile_id"],
                        "reason": cancel_result["summary"],
                    }
                )
                action = "would_cancel" if args.dry_run else "cancelled"
                print(
                    f"  {action} {record['handoff_id']} "
                    f"({record['entity_type']} -> {record['to_profile_id']}): {cancel_result['summary']}"
                )
                continue

            print(f"  run {record['handoff_id']}: {format_command(command)}")
            returncode, output = run_command(command, args.dry_run)
            if returncode == 0:
                processed.append(
                    {
                        "handoff_id": record["handoff_id"],
                        "entity_type": record["entity_type"],
                        "to_profile_id": record["to_profile_id"],
                        "command": format_command(command),
                    }
                )
                if output and not args.dry_run:
                    for line in output.splitlines()[:8]:
                        print(f"    {line}")
                continue

            if "Source registry entry not found" in (output or ""):
                cancel_result = cancel_orphaned_handoff(
                    record,
                    "source registry entry missing during execution",
                    args.dry_run,
                )
                skipped.append(
                    {
                        "handoff_id": record["handoff_id"],
                        "entity_type": record["entity_type"],
                        "to_profile_id": record["to_profile_id"],
                        "reason": cancel_result["summary"],
                    }
                )
                action = "would_cancel" if args.dry_run else "cancelled"
                print(f"    {action}: {cancel_result['summary']}")
                continue

            failed.append(
                {
                    "handoff_id": record["handoff_id"],
                    "entity_type": record["entity_type"],
                    "to_profile_id": record["to_profile_id"],
                    "command": format_command(command),
                    "output": output,
                }
            )
            print(f"    failed rc={returncode}")
            if output:
                for line in output.splitlines()[:10]:
                    print(f"    {line}")
            if not args.continue_on_error:
                break
        if failed and not args.continue_on_error:
            break

    date = args.date
    post_commands = []
    if args.build_dispatch or args.apply_dispatch:
        dispatch_packet_cmd = [
            sys.executable,
            str(SCRIPT_DIR / "build_dispatch_packet_candidate.py"),
        ]
        dispatch_patch_cmd = [
            sys.executable,
            str(SCRIPT_DIR / "build_dispatch_board_patch_candidate.py"),
        ]
        if date:
            dispatch_packet_cmd.extend(["--date", date])
            dispatch_patch_cmd.extend(["--date", date])
        post_commands.extend([dispatch_packet_cmd, dispatch_patch_cmd])
    if args.apply_dispatch:
        apply_cmd = [
            sys.executable,
            str(SCRIPT_DIR / "apply_dispatch_board_patch_candidate.py"),
        ]
        if date:
            apply_cmd.extend(["--date", date])
        post_commands.append(apply_cmd)
    if args.refresh_source_manifest:
        post_commands.append([sys.executable, str(SCRIPT_DIR.parent / "wiki" / "build_source_manifest.py")])

    for command in post_commands:
        print(f"post-run: {format_command(command)}")
        returncode, output = run_command(command, args.dry_run)
        if returncode == 0:
            if output and not args.dry_run:
                for line in output.splitlines()[:8]:
                    print(f"  {line}")
            continue
        failed.append(
            {
                "handoff_id": None,
                "entity_type": "post_run",
                "to_profile_id": None,
                "command": format_command(command),
                "output": output,
            }
        )
        print(f"  post-run failed rc={returncode}")
        if output:
            for line in output.splitlines()[:10]:
                print(f"  {line}")
        if not args.continue_on_error:
            break

    log_run(
        "run_agent_control_loop.py",
        "success" if not failed else "partial_failure",
        "agent control loop completed",
        {
            "processed_count": len(processed),
            "skipped_count": len(skipped),
            "failed_count": len(failed),
            "research_governance_mode": args.research_governance_mode,
            "build_dispatch": args.build_dispatch,
            "apply_dispatch": args.apply_dispatch,
            "refresh_source_manifest": args.refresh_source_manifest,
            "dry_run": args.dry_run,
            "processed_handoff_ids": [item["handoff_id"] for item in processed[:20]],
            "failed_commands": [item["command"] for item in failed[:10]],
        },
    )

    print("")
    print(f"processed_count={len(processed)}")
    print(f"skipped_count={len(skipped)}")
    print(f"failed_count={len(failed)}")
    if skipped:
        for item in skipped[:10]:
            print(
                f"  skipped_handoff={item['handoff_id']} "
                f"entity_type={item['entity_type']} reason={item['reason']}"
            )
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
