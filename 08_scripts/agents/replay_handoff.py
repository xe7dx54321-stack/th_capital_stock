#!/usr/bin/env python3
"""Replay or recover selected handoffs against the current agent handlers."""

import argparse
import sqlite3
import sys
from pathlib import Path

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import (
    ACTIVE_HANDOFF_STATUSES,
    DB_PATH,
    get_handoff,
    query_handoff_state,
    requeue_handoff,
    sync_handoff_state_from_disk,
)
from smr_runlog import log_run
from run_agent_control_loop import cancel_orphaned_handoff, choose_command, format_command, orphaned_source_reason, run_command


def parse_args():
    parser = argparse.ArgumentParser(description="Replay selected SMR handoffs")
    parser.add_argument("--handoff-id", action="append", help="Replay this handoff id")
    parser.add_argument("--entity-type", help="Filter by entity_type")
    parser.add_argument("--entity-id", help="Filter by entity_id")
    parser.add_argument("--to-profile-id", help="Filter by target profile")
    parser.add_argument("--from-profile-id", help="Filter by source profile")
    parser.add_argument("--status", help="Filter by current status")
    parser.add_argument("--pending-only", action="store_true", help="Only replay pending handoffs")
    parser.add_argument("--requeue-completed", action="store_true", help="Requeue non-active handoffs before replay")
    parser.add_argument("--recover-orphans", action="store_true", help="Cancel orphaned handoffs before replay")
    parser.add_argument(
        "--research-governance-mode",
        choices=["accept-only", "dry-run", "skip"],
        default="accept-only",
        help="How to handle review_queue / wiki_draft handoffs",
    )
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--continue-on-error", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def collect_records(conn, args):
    sync_handoff_state_from_disk(conn, handoff_ids=args.handoff_id or [], limit=max(args.limit, 500))
    records = []
    if args.handoff_id:
        for handoff_id in args.handoff_id:
            records.extend(query_handoff_state(conn, handoff_id=handoff_id, limit=1))
    else:
        records.extend(
            query_handoff_state(
                conn,
                status=args.status,
                to_profile_id=args.to_profile_id,
                from_profile_id=args.from_profile_id,
                entity_type=args.entity_type,
                entity_id=args.entity_id,
                limit=max(args.limit, 1),
            )
        )

    results = []
    seen = set()
    for record in records:
        handoff_id = record["handoff_id"]
        if handoff_id in seen:
            continue
        seen.add(handoff_id)
        if args.pending_only and record.get("status") != "pending":
            continue
        results.append(record)
    return results[: max(args.limit, 0)]


def main():
    args = parse_args()
    conn = sqlite3.connect(DB_PATH)
    records = collect_records(conn, args)
    if not records:
        conn.close()
        raise SystemExit("No matching handoffs found")

    processed = []
    skipped = []
    failed = []

    for record in records:
        working = record
        orphan_reason = orphaned_source_reason(working)
        if orphan_reason and args.recover_orphans:
            result = cancel_orphaned_handoff(working, orphan_reason, args.dry_run)
            skipped.append(
                {
                    "handoff_id": working["handoff_id"],
                    "reason": result["summary"],
                }
            )
            print(f"cancelled_orphan={working['handoff_id']} reason={result['summary']}")
            continue
        if orphan_reason and not args.recover_orphans:
            skipped.append(
                {
                    "handoff_id": working["handoff_id"],
                    "reason": orphan_reason,
                }
            )
            print(f"skipped_orphan={working['handoff_id']} reason={orphan_reason}")
            continue

        if working.get("status") not in ACTIVE_HANDOFF_STATUSES:
            if not args.requeue_completed:
                skipped.append(
                    {
                        "handoff_id": working["handoff_id"],
                        "reason": f"status={working.get('status')} and --requeue-completed not set",
                    }
                )
                print(
                    f"skipped_handoff={working['handoff_id']} "
                    f"reason=status={working.get('status')} requires --requeue-completed"
                )
                continue
            if args.dry_run:
                print(f"would_requeue={working['handoff_id']} status={working.get('status')}")
            else:
                working = requeue_handoff(
                    conn,
                    handoff_id=working["handoff_id"],
                    requeued_by="replay_handoff.py",
                    summary="按需重放 handoff，重新回到 pending。",
                    source="replay_handoff.py",
                )
                conn.commit()

        working = get_handoff(working["handoff_id"])
        command = choose_command(working, args.research_governance_mode)
        if command is None:
            skipped.append(
                {
                    "handoff_id": working["handoff_id"],
                    "reason": "no_safe_handler",
                }
            )
            print(f"skipped_handoff={working['handoff_id']} reason=no_safe_handler")
            continue

        print(f"run {working['handoff_id']}: {format_command(command)}")
        returncode, output = run_command(command, args.dry_run)
        if returncode == 0:
            processed.append(
                {
                    "handoff_id": working["handoff_id"],
                    "command": format_command(command),
                }
            )
            if output and not args.dry_run:
                for line in output.splitlines()[:8]:
                    print(f"  {line}")
            continue

        failed.append(
            {
                "handoff_id": working["handoff_id"],
                "command": format_command(command),
                "output": output,
            }
        )
        print(f"failed_handoff={working['handoff_id']} rc={returncode}")
        if output:
            for line in output.splitlines()[:10]:
                print(f"  {line}")
        if not args.continue_on_error:
            break

    log_run(
        "replay_handoff.py",
        "success" if not failed else "partial_failure",
        "handoff replay completed",
        {
            "processed_count": len(processed),
            "skipped_count": len(skipped),
            "failed_count": len(failed),
            "dry_run": args.dry_run,
            "requeue_completed": args.requeue_completed,
            "recover_orphans": args.recover_orphans,
            "processed_handoff_ids": [item["handoff_id"] for item in processed[:20]],
        },
    )
    conn.close()

    print(f"processed_count={len(processed)}")
    print(f"skipped_count={len(skipped)}")
    print(f"failed_count={len(failed)}")
    if failed:
        sys.exit(1)


if __name__ == "__main__":
    main()
