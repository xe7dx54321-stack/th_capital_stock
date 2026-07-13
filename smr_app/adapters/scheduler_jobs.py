from __future__ import annotations

import json
import re
import subprocess
import sys
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from .contracts import AdapterResult


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEDULER_SCRIPT = PROJECT_ROOT / "08_scripts" / "scheduler" / "run_smr_schedule_job.py"
JOB_ID_RE = re.compile(r"^[a-z][a-z0-9_]{0,63}$")


@dataclass(frozen=True)
class SchedulerJobRequest:
    job_id: str
    dry_run: bool = False
    continue_on_error: bool = False
    timeout_seconds: int = 900
    artifact_dir: Path | None = None


def _preview(value: str, limit: int = 2000) -> str:
    if len(value) <= limit:
        return value
    return value[:limit] + "\n...[truncated]"


def run_scheduler_job(request: SchedulerJobRequest) -> AdapterResult:
    if not JOB_ID_RE.fullmatch(request.job_id):
        return AdapterResult("error", error="invalid scheduler job_id")
    command = [sys.executable, str(SCHEDULER_SCRIPT), "--job", request.job_id]
    if request.dry_run:
        command.append("--dry-run")
    if request.continue_on_error:
        command.append("--continue-on-error")
    command.extend(["--timeout-seconds", str(max(1, int(request.timeout_seconds)))])
    started_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    try:
        completed = subprocess.run(
            command,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=max(1, int(request.timeout_seconds)),
            check=False,
            shell=False,
        )
        returncode = completed.returncode
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
        status = "ok" if returncode == 0 else "error"
    except subprocess.TimeoutExpired as exc:
        returncode = None
        stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
        stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
        status = "timeout"

    artifact_dir = (request.artifact_dir or PROJECT_ROOT / "10_logs" / "workflow_adapters").resolve()
    artifact_dir.mkdir(parents=True, exist_ok=True)
    log_path = artifact_dir / f"scheduler_{request.job_id}_{uuid.uuid4().hex}.json"
    log_path.write_text(
        json.dumps(
            {
                "job_id": request.job_id,
                "command": command,
                "returncode": returncode,
                "stdout": stdout,
                "stderr": stderr,
                "started_at": started_at,
                "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            },
            ensure_ascii=False,
            sort_keys=True,
        ),
        encoding="utf-8",
    )
    data = {
        "job_id": request.job_id,
        "command": command,
        "shell": False,
        "returncode": returncode,
        "stdout_preview": _preview(stdout),
        "stderr_preview": _preview(stderr),
        "log_path": str(log_path),
    }
    error = None if status == "ok" else ("scheduler job timed out" if status == "timeout" else "scheduler job failed")
    return AdapterResult(status, data, error=error)
