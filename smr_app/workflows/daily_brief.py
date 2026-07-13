from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from collections.abc import Callable
from pathlib import Path
from typing import Any

from smr_app.adapters.contracts import AdapterResult, relation_exists, table_columns
from smr_app.adapters.risk import RiskContextRequest, load_risk_context
from smr_app.adapters.scheduler_jobs import SchedulerJobRequest, run_scheduler_job
from smr_app.runtime.artifact_store import ArtifactStore
from smr_app.runtime.contracts import StageDefinition, StageResult, WorkflowContext, WorkflowDefinition


PROJECT_ROOT = Path(__file__).resolve().parents[2]
_configured_roots = os.environ.get("SMR_ARTIFACT_ROOTS", "").split(os.pathsep)
DEFAULT_ARTIFACT_ROOT = Path(_configured_roots[0]) if _configured_roots[0] else PROJECT_ROOT / "06_outputs" / "workflows"
Scheduler = Callable[[SchedulerJobRequest], AdapterResult]
CATEGORIES = ("risk", "data_health", "decision", "workflow")


def _hash(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _validate(context: WorkflowContext) -> StageResult:
    allow_network = context.input_data.get("allow_network", False)
    run_refresh_job = context.input_data.get("run_refresh_job", False)
    if not isinstance(allow_network, bool) or allow_network:
        raise ValueError("daily_brief only supports allow_network=false")
    if not isinstance(run_refresh_job, bool):
        raise ValueError("run_refresh_job must be a boolean")
    context.state.update({"allow_network": False, "run_refresh_job": run_refresh_job})
    return StageResult.completed("Daily brief input validated")


def _run_refresh(scheduler: Scheduler):
    def handler(context: WorkflowContext) -> StageResult:
        request = SchedulerJobRequest("daily_report", dry_run=not context.state["run_refresh_job"])
        result = scheduler(request)
        context.state["scheduler"] = result.to_dict()
        return StageResult.completed(
            "Daily report adapter completed" if result.ok else "Daily report adapter returned a warning",
            {"scheduler_status": result.status, "scheduler_job_id": request.job_id},
        )

    return handler


def _decision_items(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    columns = table_columns(conn, "decision_ledger")
    if not columns or not {"ticker", "status"}.issubset(columns):
        return []
    id_column = "decision_id" if "decision_id" in columns else "recommendation_id" if "recommendation_id" in columns else "ticker"
    time_column = "updated_at" if "updated_at" in columns else "decision_time" if "decision_time" in columns else "ticker"
    action = "action" if "action" in columns else "NULL"
    rows = conn.execute(
        f"SELECT {id_column}, ticker, status, {action}, {time_column} FROM decision_ledger ORDER BY {time_column} DESC LIMIT 100"
    ).fetchall()
    return [
        {
            "identity": f"decision:{row[0] or row[1]}",
            "ticker": row[1],
            "status": row[2],
            "action": row[3],
            "updated_at": row[4],
        }
        for row in rows
    ]


def _workflow_items(conn: sqlite3.Connection, current_run_id: str) -> list[dict[str, Any]]:
    if not relation_exists(conn, "workflow_runs"):
        return []
    rows = conn.execute(
        """
        SELECT run_id, workflow_id, status, completed_at, error_code
        FROM workflow_runs
        WHERE run_id<>? AND status IN ('failed', 'waiting_review')
        ORDER BY datetime(COALESCE(completed_at, created_at)) DESC LIMIT 30
        """,
        (current_run_id,),
    ).fetchall()
    return [
        {
            "identity": f"workflow:{row[0]}", "run_id": row[0], "workflow_id": row[1],
            "status": row[2], "completed_at": row[3], "error_code": row[4],
        }
        for row in rows
    ]


def _previous_snapshot(conn: sqlite3.Connection, current_run_id: str) -> dict[str, str]:
    row = conn.execute(
        """
        SELECT summary_json FROM workflow_runs
        WHERE workflow_id='daily_brief' AND run_id<>? AND status='completed'
        ORDER BY datetime(completed_at) DESC, rowid DESC LIMIT 1
        """,
        (current_run_id,),
    ).fetchone()
    if not row:
        return {}
    try:
        return dict((json.loads(row[0] or "{}") or {}).get("snapshot_signatures") or {})
    except (TypeError, ValueError):
        return {}


def _collect(max_items_per_category: int):
    def handler(context: WorkflowContext) -> StageResult:
        conn = sqlite3.connect(context.db_path)
        try:
            risk = load_risk_context(conn, RiskContextRequest(limit=200))
            risk_items: dict[str, dict[str, Any]] = {}
            for alert in risk.data.get("alerts") or []:
                identity = f"risk:{alert.get('alert_type')}:{alert.get('ticker') or 'global'}"
                risk_items[identity] = {"identity": identity, **alert}
            health_items: dict[str, dict[str, Any]] = {}
            for item in (risk.data.get("data_health") or {}).get("items") or []:
                identity = f"health:{item.get('market') or 'global'}:{item.get('data_type') or 'unknown'}"
                health_items[identity] = {"identity": identity, **item}
            category_maps = {
                "risk": risk_items,
                "data_health": health_items,
                "decision": {item["identity"]: item for item in _decision_items(conn)},
                "workflow": {item["identity"]: item for item in _workflow_items(conn, context.run_id)},
            }
            previous = _previous_snapshot(conn, context.run_id)
        finally:
            conn.close()

        snapshot: dict[str, str] = {}
        categories: dict[str, list[dict[str, Any]]] = {}
        for category in CATEGORIES:
            changed: list[dict[str, Any]] = []
            for identity, item in category_maps[category].items():
                signature = _hash({key: value for key, value in item.items() if key not in {"alert_id", "decision_time", "updated_at"}})
                snapshot[identity] = signature
                if previous.get(identity) != signature:
                    changed.append(item)
            categories[category] = changed[:max_items_per_category]

        summary = {
            "change_count": sum(len(items) for items in categories.values()),
            "categories": categories,
            "category_limits": {category: max_items_per_category for category in CATEGORIES},
            "snapshot_signatures": snapshot,
            "scheduler": context.state.get("scheduler"),
            "allow_network": False,
        }
        context.state["summary"] = summary
        return StageResult.completed("Material daily changes collected", summary)

    return handler


def _render(summary: dict[str, Any]) -> str:
    lines = ["# Daily Research Brief", "", f"Material changes: **{summary['change_count']}**", ""]
    labels = {"risk": "Risk alerts", "data_health": "Data health", "decision": "Decision ledger", "workflow": "Workflow exceptions"}
    for category in CATEGORIES:
        lines.extend([f"## {labels[category]}", ""])
        items = summary["categories"][category]
        if not items:
            lines.append("- No material change since the previous brief.")
        for item in items:
            subject = item.get("ticker") or item.get("run_id") or item.get("identity")
            detail = item.get("message") or item.get("status") or item.get("freshness_status") or "changed"
            lines.append(f"- **{subject}** — {detail}")
        lines.append("")
    lines.extend(["---", "Local-only research aid; no orders were placed.", ""])
    return "\n".join(lines)


def _write(artifact_root: Path):
    def handler(context: WorkflowContext) -> StageResult:
        run_dir = artifact_root.resolve() / context.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        path = run_dir / "daily_brief.md"
        path.write_text(_render(context.state["summary"]), encoding="utf-8")
        conn = sqlite3.connect(context.db_path)
        try:
            artifact = ArtifactStore(conn, [artifact_root]).register_artifact(
                context.run_id, "daily_brief", "Daily research brief", path, "text/markdown",
                metadata={"change_count": context.state["summary"]["change_count"]},
            )
        finally:
            conn.close()
        summary = {**context.state["summary"], "artifacts": [artifact["artifact_id"]]}
        context.state["summary"] = summary
        return StageResult.completed("Daily brief persisted", summary, artifacts=(artifact,))

    return handler


def daily_brief_definition(
    *, artifact_root: str | Path | None = None, scheduler: Scheduler = run_scheduler_job,
    max_items_per_category: int = 5,
) -> WorkflowDefinition:
    root = Path(artifact_root) if artifact_root is not None else DEFAULT_ARTIFACT_ROOT
    cap = max(1, min(int(max_items_per_category), 20))
    return WorkflowDefinition(
        workflow_id="daily_brief", title="Daily brief", description="Summarize material local research changes.",
        input_schema={
            "type": "object", "properties": {"allow_network": {"type": "boolean", "default": False}, "run_refresh_job": {"type": "boolean", "default": False}},
            "additionalProperties": False,
        },
        stages=(
            StageDefinition("validate_input", _validate),
            StageDefinition("scheduler_adapter", _run_refresh(scheduler)),
            StageDefinition("collect_changes", _collect(cap)),
            StageDefinition("write_brief", _write(root)),
        ),
    )
