#!/usr/bin/env python3
"""Install macOS launchd jobs for SMR project-owned agent schedules."""

from __future__ import annotations

import argparse
import json
import os
import plistlib
import subprocess
import sys
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parents[2]
REGISTRY_PATH = PROJECT_ROOT / "12_smr_agents" / "schedules" / "agent_schedule_registry.json"
RUNNER_PATH = PROJECT_ROOT / "08_scripts" / "scheduler" / "run_agent_schedule.py"
PLIST_DIR = Path.home() / "Library" / "LaunchAgents"
LOG_DIR = PROJECT_ROOT / "10_logs" / "launchd"
LABEL_PREFIX = "com.tonghang.smr.agent"
LAUNCHD_PATH = "/Library/Frameworks/Python.framework/Versions/3.14/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"


def load_registry() -> dict:
    return json.loads(REGISTRY_PATH.read_text(encoding="utf-8"))


def schedules() -> list[dict]:
    return load_registry().get("schedules") or []


def label_for(item: dict) -> str:
    return f"{LABEL_PREFIX}.{str(item['schedule_id']).replace('_', '-')}"


def plist_path_for(item: dict) -> Path:
    return PLIST_DIR / f"{label_for(item)}.plist"


def launchd_weekdays(item: dict) -> list[int]:
    mapping = (load_registry().get("weekday_launchd_values") or {})
    return [int(mapping[name]) for name in item.get("weekdays", [])]


def build_plist(item: dict) -> dict:
    schedule_id = item["schedule_id"]
    start_calendar_interval = [
        {
            "Weekday": weekday,
            "Hour": int(item["hour"]),
            "Minute": int(item["minute"]),
        }
        for weekday in launchd_weekdays(item)
    ]
    return {
        "Label": label_for(item),
        "ProgramArguments": [
            sys.executable,
            str(RUNNER_PATH),
            "--schedule-id",
            schedule_id,
        ],
        "WorkingDirectory": str(PROJECT_ROOT),
        "EnvironmentVariables": {
            "SMR_ROOT": str(PROJECT_ROOT),
            "PATH": LAUNCHD_PATH,
        },
        "RunAtLoad": False,
        "StartCalendarInterval": start_calendar_interval,
        "StandardOutPath": str(LOG_DIR / f"{schedule_id}.out.log"),
        "StandardErrorPath": str(LOG_DIR / f"{schedule_id}.err.log"),
    }


def write_plist(item: dict, dry_run: bool) -> Path:
    path = plist_path_for(item)
    payload = build_plist(item)
    print(f"{label_for(item)} -> {path}")
    if dry_run:
        print(plistlib.dumps(payload).decode("utf-8").strip())
        return path

    PLIST_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    path.write_bytes(plistlib.dumps(payload, sort_keys=False))
    return path


def run_launchctl(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(args, capture_output=True, text=True)


def load_plist(item: dict) -> int:
    uid = os.getuid()
    domain = f"gui/{uid}"
    path = plist_path_for(item)
    label = label_for(item)

    run_launchctl(["launchctl", "bootout", domain, str(path)])
    completed = run_launchctl(["launchctl", "bootstrap", domain, str(path)])
    if completed.returncode != 0:
        print(f"load failed: {label}", file=sys.stderr)
        print((completed.stderr or completed.stdout).strip(), file=sys.stderr)
        return completed.returncode
    print(f"loaded: {label}")
    return 0


def unload_plist(item: dict) -> int:
    uid = os.getuid()
    domain = f"gui/{uid}"
    path = plist_path_for(item)
    completed = run_launchctl(["launchctl", "bootout", domain, str(path)])
    if completed.returncode != 0:
        print(f"unload warning: {label_for(item)} {(completed.stderr or completed.stdout).strip()}")
        return completed.returncode
    print(f"unloaded: {label_for(item)}")
    return 0


def print_status(item: dict) -> int:
    uid = os.getuid()
    completed = run_launchctl(["launchctl", "print", f"gui/{uid}/{label_for(item)}"])
    status = "loaded" if completed.returncode == 0 else "not_loaded"
    print(f"{label_for(item)}\t{status}\t{plist_path_for(item)}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Deploy SMR agent schedules to macOS launchd")
    parser.add_argument("--install", action="store_true", help="Write LaunchAgent plist files")
    parser.add_argument("--load", action="store_true", help="Load LaunchAgent plist files after writing")
    parser.add_argument("--unload", action="store_true", help="Unload LaunchAgent plist files")
    parser.add_argument("--status", action="store_true", help="Print launchd load status")
    parser.add_argument("--dry-run", action="store_true", help="Print generated plists without writing")
    args = parser.parse_args()

    if not any([args.install, args.unload, args.status, args.dry_run]):
        parser.error("choose --install, --unload, --status, or --dry-run")

    exit_code = 0
    for item in schedules():
        if args.unload:
            rc = unload_plist(item)
            exit_code = exit_code or (0 if rc in {0, 3, 5} else rc)
            continue
        if args.status:
            print_status(item)
            continue
        if args.install or args.dry_run:
            write_plist(item, dry_run=args.dry_run)
            if args.load and not args.dry_run:
                exit_code = exit_code or load_plist(item)

    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
