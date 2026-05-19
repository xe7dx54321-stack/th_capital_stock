#!/usr/bin/env python3
"""Run SMR scheduled jobs through the project-owned agent runtime."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parents[2]
REGISTRY_PATH = PROJECT_ROOT / "12_smr_agents" / "schedules" / "agent_schedule_registry.json"
JOB_RUNNER = PROJECT_ROOT / "08_scripts" / "scheduler" / "run_smr_schedule_job.py"
PROFILE_DIR = PROJECT_ROOT / "12_smr_agents" / "profiles"


def load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def schedules() -> list[dict]:
    return load_registry().get("schedules") or []


def schedule_by_id(schedule_id: str) -> dict:
    for item in schedules():
        if item.get("schedule_id") == schedule_id:
            return item
    raise SystemExit(f"unknown schedule_id: {schedule_id}")


def profile_exists(profile_id: str) -> bool:
    return bool(profile_id and (PROFILE_DIR / f"{profile_id}.json").exists())


def validate_schedule(item: dict) -> list[str]:
    errors = []
    if not item.get("schedule_id"):
        errors.append("missing schedule_id")
    if not item.get("job_id"):
        errors.append(f"{item.get('schedule_id') or '<unknown>'}: missing job_id")
    if not profile_exists(item.get("lead_profile_id")):
        errors.append(f"{item.get('schedule_id')}: missing lead profile {item.get('lead_profile_id')}")
    for profile_id in item.get("operator_profile_ids") or []:
        if not profile_exists(profile_id):
            errors.append(f"{item.get('schedule_id')}: missing operator profile {profile_id}")
    return errors


def validate_registry() -> list[str]:
    errors = []
    seen = set()
    for item in schedules():
        schedule_id = item.get("schedule_id")
        if schedule_id in seen:
            errors.append(f"duplicate schedule_id: {schedule_id}")
        seen.add(schedule_id)
        errors.extend(validate_schedule(item))
    return errors


def list_schedules() -> None:
    for item in schedules():
        weekdays = ",".join(item.get("weekdays") or [])
        print(
            "{schedule_id}\t{time}\t{job_id}\t{lead}\t{operators}\t{label}".format(
                schedule_id=item["schedule_id"],
                time=f"{weekdays} {int(item['hour']):02d}:{int(item['minute']):02d}",
                job_id=item["job_id"],
                lead=item["lead_profile_id"],
                operators=",".join(item.get("operator_profile_ids") or []),
                label=item["label"],
            )
        )


def build_job_command(item: dict, dry_run: bool) -> list[str]:
    command = [
        sys.executable,
        str(JOB_RUNNER),
        "--job",
        item["job_id"],
    ]
    if item.get("continue_on_error", True):
        command.append("--continue-on-error")
    if item.get("timeout_seconds"):
        command.extend(["--timeout-seconds", str(item["timeout_seconds"])])
    if dry_run:
        command.append("--dry-run")
    return command


def build_agent_env(item: dict) -> dict:
    env = os.environ.copy()
    env.update(
        {
            "SMR_ROOT": str(PROJECT_ROOT),
            "SMR_RUN_TRIGGER": "agent_schedule",
            "SMR_SCHEDULE_ID": item["schedule_id"],
            "SMR_SCHEDULE_LABEL": item.get("label") or item["schedule_id"],
            "SMR_LEAD_PROFILE_ID": item["lead_profile_id"],
            "SMR_OPERATOR_PROFILE_IDS": ",".join(item.get("operator_profile_ids") or []),
        }
    )
    return env


def run_schedule(item: dict, dry_run: bool) -> int:
    errors = validate_schedule(item)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2

    command = build_job_command(item, dry_run)
    print(f"[agent_schedule] {item['schedule_id']} | {item['label']}")
    print(f"lead_profile_id={item['lead_profile_id']}")
    print(f"operator_profile_ids={','.join(item.get('operator_profile_ids') or [])}")
    print(f"job_id={item['job_id']}")
    print(f"command={subprocess.list2cmdline(command)}")
    print("")

    completed = subprocess.run(command, cwd=str(PROJECT_ROOT), env=build_agent_env(item))
    return completed.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Run an SMR schedule through the agent runtime")
    parser.add_argument("--schedule-id", help="Schedule id from agent_schedule_registry.json")
    parser.add_argument("--list", action="store_true", help="List configured agent schedules")
    parser.add_argument("--validate", action="store_true", help="Validate schedule registry and profile references")
    parser.add_argument("--dry-run", action="store_true", help="Show and dry-run the underlying job command")
    args = parser.parse_args()

    if args.list:
        list_schedules()
        return 0

    errors = validate_registry()
    if args.validate:
        if errors:
            for error in errors:
                print(f"ERROR: {error}", file=sys.stderr)
            return 1
        print(f"agent schedule registry ok: {REGISTRY_PATH}")
        print(f"schedule_count={len(schedules())}")
        return 0

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    if not args.schedule_id:
        parser.error("--schedule-id is required unless --list or --validate is used")

    return run_schedule(schedule_by_id(args.schedule_id), args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
