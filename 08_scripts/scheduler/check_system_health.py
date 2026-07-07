#!/usr/bin/env python3
"""System health check for maintenance chain (read-only mode)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parents[2]


def run_command(cmd: str, **kwargs) -> tuple[int, str, str]:
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True, **kwargs)
    return result.returncode, result.stdout, result.stderr


def check_git_status() -> dict:
    os.chdir(PROJECT_ROOT)
    rc, out, err = run_command("git status --short")
    rc2, branch_out, _ = run_command("git branch --show-current")
    rc3, commit_out, _ = run_command("git rev-parse --short HEAD")
    return {
        "status": "ok" if rc == 0 else "error",
        "branch": branch_out.strip(),
        "commit": commit_out.strip(),
        "unstaged_changes": len(out.strip().split("\n")) if out.strip() else 0,
        "output": out.strip()[:500],
    }


def check_disk_usage() -> dict:
    rc, out, err = run_command("df -h /")
    lines = out.strip().split("\n")
    if len(lines) >= 2:
        parts = lines[1].split()
        return {
            "status": "ok" if rc == 0 else "error",
            "filesystem": parts[0],
            "size": parts[1],
            "used": parts[2],
            "available": parts[3],
            "use_percent": parts[4],
            "mounted_on": parts[5],
        }
    return {"status": "error", "message": "Failed to parse df output"}


def check_db_size() -> dict:
    db_dir = PROJECT_ROOT / "01_data"
    total_size = 0
    db_files = []
    for db_file in db_dir.rglob("*.db"):
        size = db_file.stat().st_size
        total_size += size
        db_files.append({"name": str(db_file.relative_to(PROJECT_ROOT)), "size_bytes": size})
    return {
        "status": "ok",
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "db_files": db_files,
        "db_count": len(db_files),
    }


def check_quarantine_size() -> dict:
    quarantine_dir = PROJECT_ROOT / "quarantine"
    if not quarantine_dir.exists():
        return {"status": "ok", "exists": False, "total_size_bytes": 0, "file_count": 0}
    total_size = 0
    file_count = 0
    for f in quarantine_dir.rglob("*"):
        if f.is_file():
            total_size += f.stat().st_size
            file_count += 1
    return {
        "status": "ok",
        "exists": True,
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / (1024 * 1024), 2),
        "file_count": file_count,
    }


def check_log_presence() -> dict:
    log_dir = PROJECT_ROOT / "10_logs"
    log_present = {}
    for sub_dir in ["control_tower", "dashboard", "scheduler"]:
        sub_path = log_dir / sub_dir
        if sub_path.exists():
            recent_files = list(sub_path.glob("*.log")) + list(sub_path.glob("*.json"))
            recent_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            log_present[sub_dir] = {
                "exists": True,
                "file_count": len(recent_files),
                "recent_files": [str(f.relative_to(PROJECT_ROOT)) for f in recent_files[:3]],
            }
        else:
            log_present[sub_dir] = {"exists": False, "file_count": 0}
    return {"status": "ok", "logs": log_present}


def check_scheduler_config() -> dict:
    registry_path = PROJECT_ROOT / "12_smr_agents" / "schedules" / "agent_schedule_registry.json"
    if not registry_path.exists():
        return {"status": "error", "message": "Registry file not found"}
    try:
        with open(registry_path, "r") as f:
            registry = json.load(f)
        schedules = registry.get("schedules", [])
        enabled_count = sum(1 for s in schedules if s.get("enabled", False))
        return {
            "status": "ok",
            "total_schedules": len(schedules),
            "enabled_schedules": enabled_count,
            "registry_path": str(registry_path.relative_to(PROJECT_ROOT)),
        }
    except json.JSONDecodeError as e:
        return {"status": "error", "message": f"JSON parse error: {e}"}


def main() -> None:
    report = {
        "started_at": datetime.now().isoformat(),
        "hostname": os.uname().nodename,
        "project_path": str(PROJECT_ROOT),
        "checks": {},
    }

    report["checks"]["git_status"] = check_git_status()
    report["checks"]["disk_usage"] = check_disk_usage()
    report["checks"]["db_size"] = check_db_size()
    report["checks"]["quarantine_size"] = check_quarantine_size()
    report["checks"]["log_presence"] = check_log_presence()
    report["checks"]["scheduler_config"] = check_scheduler_config()

    all_ok = all(c.get("status") == "ok" for c in report["checks"].values())
    report["status"] = "ok" if all_ok else "warning"
    report["finished_at"] = datetime.now().isoformat()

    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
