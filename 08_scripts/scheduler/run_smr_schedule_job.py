#!/usr/bin/env python3
"""Run named SMR scheduled jobs with locking and structured logs."""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parents[2]
LIB_DIR = PROJECT_ROOT / "08_scripts" / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_runlog import log_run

LOG_ROOT = PROJECT_ROOT / "10_logs" / "scheduler"
LOCK_ROOT = LOG_ROOT / "locks"
RUN_ROOT = LOG_ROOT / "runs"
SCRIPT_NAME = "run_smr_schedule_job.py"
PYTHON = sys.executable


@dataclass(frozen=True)
class JobSpec:
    job_id: str
    label: str
    description: str
    commands: tuple[tuple[str, ...], ...]


def py(script_rel_path: str, *args: str) -> tuple[str, ...]:
    return (PYTHON, str(PROJECT_ROOT / script_rel_path), *args)


JOB_SPECS: dict[str, JobSpec] = {
    "morning_us": JobSpec(
        job_id="morning_us",
        label="晨间美股链",
        description="同步美股数据、信号和动态池，并推动下游解释候选刷新。",
        commands=(
            py("08_scripts/stock_pool/sync_watchlist.py"),
            py("08_scripts/data_harvester/ah_daily_bar.py", "--days", "5", "--us-only"),
            py("08_scripts/us_signal_harvester/earnings_monitor.py"),
            py("08_scripts/factor_engine/us_linkage.py"),
            py("08_scripts/stock_pool/reconcile_dynamic_pool.py"),
            py("08_scripts/research/build_price_range_forecast_snapshot.py"),
            py("08_scripts/agents/run_agent_control_loop.py", "--research-governance-mode", "skip", "--build-dispatch"),
        ),
    ),
    "deep_market_scan": JobSpec(
        job_id="deep_market_scan",
        label="深度市场扫描",
        description="按主题聚合全网公开信息，刷新 AI / 光通信 / 新能源 / scale up / scale out 的机会挖掘结果。",
        commands=(
            py("08_scripts/wiki/fetch_marketscreener_analyst_signals.py"),
            py("08_scripts/research/build_deep_market_analysis_snapshot.py"),
        ),
    ),
    "preopen_report": JobSpec(
        job_id="preopen_report",
        label="盘前简报链",
        description="刷新日报快照、物化正式盘前简报，并同步 dispatch 候选。",
        commands=(
            py("08_scripts/reporting/build_market_flow_anomaly_snapshot.py"),
            py("08_scripts/research/build_price_range_forecast_snapshot.py"),
            py("08_scripts/reporting/snapshot_daily_reporting.py"),
            py("08_scripts/reporting/materialize_daily_report.py"),
            py("08_scripts/reporting/snapshot_daily_reporting.py"),
            py("08_scripts/agents/run_agent_control_loop.py", "--research-governance-mode", "skip", "--build-dispatch"),
        ),
    ),
    "afternoon_close": JobSpec(
        job_id="afternoon_close",
        label="午后收盘链",
        description="刷新 A/H 行情、因子、研究、池子和组合动作候选。",
        commands=(
            py("08_scripts/stock_pool/sync_watchlist.py"),
            py("08_scripts/data_harvester/ah_daily_bar.py", "--days", "5", "--a-only"),
            py("08_scripts/data_harvester/ah_daily_bar.py", "--days", "5", "--hk-only"),
            py("08_scripts/factor_engine/trend.py"),
            py("08_scripts/factor_engine/fundamental.py"),
            py("08_scripts/factor_engine/us_linkage.py"),
            py("08_scripts/research/generate_trend_batch.py"),
            py("08_scripts/stock_pool/reconcile_dynamic_pool.py"),
            py("08_scripts/research/snapshot_stock_objective_monitor.py"),
            py("08_scripts/research/build_strategy_watch_cards.py"),
            py("08_scripts/research/build_price_range_forecast_snapshot.py"),
            py("08_scripts/portfolio/build_rotation_candidates.py"),
            py("08_scripts/portfolio/build_rotation_execution_plan.py"),
            py("08_scripts/portfolio/build_portfolio_action_memo.py"),
            py("08_scripts/agents/run_agent_control_loop.py", "--research-governance-mode", "skip", "--build-dispatch"),
        ),
    ),
    "afternoon_refresh": JobSpec(
        job_id="afternoon_refresh",
        label="午后二次刷新",
        description="补跑因子和研究候选，保证收盘后第二轮结果收口。",
        commands=(
            py("08_scripts/factor_engine/trend.py"),
            py("08_scripts/factor_engine/fundamental.py"),
            py("08_scripts/factor_engine/us_linkage.py"),
            py("08_scripts/research/generate_trend_batch.py"),
            py("08_scripts/stock_pool/reconcile_dynamic_pool.py"),
            py("08_scripts/research/snapshot_stock_objective_monitor.py"),
            py("08_scripts/research/build_strategy_watch_cards.py"),
            py("08_scripts/research/build_price_range_forecast_snapshot.py"),
            py("08_scripts/portfolio/build_rotation_candidates.py"),
            py("08_scripts/portfolio/build_rotation_execution_plan.py"),
            py("08_scripts/portfolio/build_portfolio_action_memo.py"),
            py("08_scripts/agents/run_agent_control_loop.py", "--research-governance-mode", "skip", "--build-dispatch"),
        ),
    ),
    "opportunity_radar": JobSpec(
        job_id="opportunity_radar",
        label="主动机会雷达链",
        description="把异动、因子、研究池、轻量回测和攻防推演收敛成纸面观察单。",
        commands=(
            py("08_scripts/reporting/build_market_flow_anomaly_snapshot.py"),
            py("08_scripts/opportunity/build_opportunity_radar_snapshot.py"),
            py("08_scripts/opportunity/build_strategy_evidence_snapshot.py", "--limit", "16"),
            py("08_scripts/opportunity/build_thesis_attack_defense_snapshot.py", "--limit", "12"),
            py("08_scripts/opportunity/build_paper_trade_watchlist.py", "--limit", "8"),
            py("08_scripts/agents/run_agent_control_loop.py", "--research-governance-mode", "skip", "--build-dispatch"),
        ),
    ),
    "portfolio_review": JobSpec(
        job_id="portfolio_review",
        label="持仓复盘",
        description="更新持仓盈亏并推动可能出现的风险/调仓解释候选。",
        commands=(
            py("08_scripts/portfolio/pnl.py"),
            py("08_scripts/agents/run_agent_control_loop.py", "--research-governance-mode", "skip", "--build-dispatch"),
        ),
    ),
    "daily_report": JobSpec(
        job_id="daily_report",
        label="晚间日报链",
        description="物化正式日报，并把日报解释与调度候选同步出来。",
        commands=(
            py("08_scripts/reporting/build_market_flow_anomaly_snapshot.py"),
            py("08_scripts/research/build_price_range_forecast_snapshot.py"),
            py("08_scripts/reporting/snapshot_daily_reporting.py"),
            py("08_scripts/reporting/materialize_daily_report.py"),
            py("08_scripts/reporting/snapshot_daily_reporting.py"),
            py("08_scripts/agents/run_agent_control_loop.py", "--research-governance-mode", "skip", "--build-dispatch"),
        ),
    ),
    "risk_review": JobSpec(
        job_id="risk_review",
        label="晚间风控链",
        description="刷新风控快照，并推动风险解释候选与调度候选刷新。",
        commands=(
            py("08_scripts/risk_engine/monitor.py"),
            py("08_scripts/risk_engine/build_trade_risk_decision_snapshot.py"),
            py("08_scripts/agents/run_agent_control_loop.py", "--research-governance-mode", "skip", "--build-dispatch"),
        ),
    ),
    "next_day_plan": JobSpec(
        job_id="next_day_plan",
        label="次日计划链",
        description="抽取未来催化日历，并刷新当日 dispatch 候选收口。",
        commands=(
            py("08_scripts/events/build_upcoming_event_calendar.py"),
            py("08_scripts/agents/build_dispatch_packet_candidate.py"),
            py("08_scripts/agents/build_dispatch_board_patch_candidate.py"),
        ),
    ),
}


def now_ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def ensure_dirs() -> None:
    LOCK_ROOT.mkdir(parents=True, exist_ok=True)
    RUN_ROOT.mkdir(parents=True, exist_ok=True)


def process_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


@contextmanager
def job_lock(job_id: str):
    ensure_dirs()
    lock_path = LOCK_ROOT / f"{job_id}.lock"
    payload = {
        "job_id": job_id,
        "pid": os.getpid(),
        "started_at": now_ts(),
    }
    if lock_path.exists():
        try:
            existing = json.loads(lock_path.read_text(encoding="utf-8"))
        except Exception:
            existing = {}
        existing_pid = int(existing.get("pid") or 0)
        if process_alive(existing_pid):
            raise SystemExit(f"job already running: {job_id} (pid={existing_pid})")
        lock_path.unlink(missing_ok=True)
    lock_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    try:
        yield lock_path
    finally:
        lock_path.unlink(missing_ok=True)


def command_label(command: tuple[str, ...]) -> str:
    if len(command) >= 2 and command[0] == PYTHON:
        try:
            return str(Path(command[1]).relative_to(PROJECT_ROOT))
        except ValueError:
            return command[1]
    return command[0]


def command_shell(command: tuple[str, ...]) -> str:
    return subprocess.list2cmdline(list(command))


def split_csv(value: str | None) -> list[str]:
    return [item.strip() for item in (value or "").split(",") if item.strip()]


def execution_context() -> dict:
    return {
        "trigger": os.environ.get("SMR_RUN_TRIGGER") or "manual",
        "schedule_id": os.environ.get("SMR_SCHEDULE_ID") or "",
        "schedule_label": os.environ.get("SMR_SCHEDULE_LABEL") or "",
        "lead_profile_id": os.environ.get("SMR_LEAD_PROFILE_ID") or "",
        "operator_profile_ids": split_csv(os.environ.get("SMR_OPERATOR_PROFILE_IDS")),
    }


def run_command(command: tuple[str, ...], timeout_seconds: int | None = None) -> dict:
    started = time.time()
    completed = subprocess.run(
        list(command),
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
    )
    ended = time.time()
    return {
        "command": list(command),
        "label": command_label(command),
        "shell": command_shell(command),
        "returncode": completed.returncode,
        "stdout": completed.stdout or "",
        "stderr": completed.stderr or "",
        "duration_seconds": round(ended - started, 2),
    }


def write_run_artifacts(
    job: JobSpec,
    results: list[dict],
    status: str,
    started_at: str,
    finished_at: str,
    context: dict,
) -> dict:
    ensure_dirs()
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = RUN_ROOT / f"{stamp}__{job.job_id}"
    run_dir.mkdir(parents=True, exist_ok=True)

    summary = {
        "job_id": job.job_id,
        "label": job.label,
        "description": job.description,
        "status": status,
        "started_at": started_at,
        "finished_at": finished_at,
        "execution_context": context,
        "command_count": len(results),
        "failed_count": sum(1 for item in results if item.get("returncode") not in (0, None)),
        "results": [
            {
                "label": item["label"],
                "shell": item["shell"],
                "returncode": item["returncode"],
                "duration_seconds": item["duration_seconds"],
            }
            for item in results
        ],
    }
    (run_dir / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    lines = [
        f"# {job.label}",
        "",
        f"- job_id: `{job.job_id}`",
        f"- status: `{status}`",
        f"- started_at: `{started_at}`",
        f"- finished_at: `{finished_at}`",
        f"- trigger: `{context.get('trigger') or ''}`",
        f"- schedule_id: `{context.get('schedule_id') or ''}`",
        f"- lead_profile_id: `{context.get('lead_profile_id') or ''}`",
        f"- operator_profile_ids: `{', '.join(context.get('operator_profile_ids') or [])}`",
        "",
    ]
    for index, item in enumerate(results, start=1):
        lines.extend(
            [
                f"## Step {index}: {item['label']}",
                "",
                f"- command: `{item['shell']}`",
                f"- returncode: `{item['returncode']}`",
                f"- duration_seconds: `{item['duration_seconds']}`",
                "",
            ]
        )
        stdout = item.get("stdout", "").strip()
        stderr = item.get("stderr", "").strip()
        if stdout:
            lines.extend(["### stdout", "", "```text", stdout, "```", ""])
        if stderr:
            lines.extend(["### stderr", "", "```text", stderr, "```", ""])
    (run_dir / "run.md").write_text("\n".join(lines), encoding="utf-8")
    return {
        "run_dir": str(run_dir),
        "summary_path": str(run_dir / "summary.json"),
        "run_md_path": str(run_dir / "run.md"),
    }


def execute_job(job: JobSpec, dry_run: bool, continue_on_error: bool, timeout_seconds: int | None) -> int:
    started_at = now_ts()
    results: list[dict] = []
    status = "success"
    context = execution_context()

    print(f"[{job.job_id}] {job.label}")
    print(job.description)
    if context.get("trigger") != "manual":
        print(
            "agent_context: "
            f"trigger={context.get('trigger')} "
            f"schedule_id={context.get('schedule_id')} "
            f"lead={context.get('lead_profile_id')} "
            f"operators={','.join(context.get('operator_profile_ids') or [])}"
        )
    print("")

    for index, command in enumerate(job.commands, start=1):
        print(f"{index}. {command_shell(command)}")
        if dry_run:
            results.append(
                {
                    "command": list(command),
                    "label": command_label(command),
                    "shell": command_shell(command),
                    "returncode": None,
                    "stdout": "",
                    "stderr": "",
                    "duration_seconds": 0.0,
                }
            )
            continue

        result = run_command(command, timeout_seconds=timeout_seconds)
        results.append(result)
        print(f"   rc={result['returncode']} duration={result['duration_seconds']}s")
        if result["returncode"] != 0:
            status = "partial_failure"
            preview = (result.get("stderr") or result.get("stdout") or "").strip().splitlines()[:8]
            for line in preview:
                print(f"   {line}")
            if not continue_on_error:
                break

    finished_at = now_ts()
    artifact_paths = write_run_artifacts(job, results, "dry_run" if dry_run else status, started_at, finished_at, context)
    log_run(
        SCRIPT_NAME,
        "success" if dry_run or status == "success" else "partial_failure",
        "scheduled job executed",
        {
            "job_id": job.job_id,
            "label": job.label,
            "dry_run": dry_run,
            "execution_context": context,
            "command_count": len(results),
            "failed_count": sum(1 for item in results if item.get("returncode") not in (0, None)),
            **artifact_paths,
        },
    )

    print("")
    print(f"run_md_path={artifact_paths['run_md_path']}")
    print(f"summary_path={artifact_paths['summary_path']}")

    if dry_run:
        return 0
    if status != "success":
        return 1
    return 0


def list_jobs() -> None:
    for job_id, job in JOB_SPECS.items():
        print(f"{job_id}\t{job.label}\t{job.description}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run named SMR scheduled jobs")
    parser.add_argument("--job", choices=sorted(JOB_SPECS), help="Job id to run")
    parser.add_argument("--list", action="store_true", help="List available jobs")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without executing them")
    parser.add_argument("--continue-on-error", action="store_true", help="Continue remaining commands after a failure")
    parser.add_argument("--timeout-seconds", type=int, help="Per-command timeout in seconds")
    args = parser.parse_args()

    if args.list:
        list_jobs()
        return 0
    if not args.job:
        parser.error("--job is required unless --list is used")

    job = JOB_SPECS[args.job]
    with job_lock(job.job_id):
        return execute_job(
            job=job,
            dry_run=args.dry_run,
            continue_on_error=args.continue_on_error,
            timeout_seconds=args.timeout_seconds,
        )


if __name__ == "__main__":
    raise SystemExit(main())
