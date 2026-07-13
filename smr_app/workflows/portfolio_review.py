from __future__ import annotations

import json
import os
import sqlite3
from collections import Counter, defaultdict
from collections.abc import Callable
from pathlib import Path
from typing import Any

from smr_app.adapters.contracts import AdapterResult, relation_exists
from smr_app.adapters.decisions import DecisionContextRequest, load_decision_context
from smr_app.adapters.scheduler_jobs import SchedulerJobRequest, run_scheduler_job
from smr_app.runtime.artifact_store import ArtifactStore
from smr_app.runtime.contracts import StageDefinition, StageResult, WorkflowContext, WorkflowDefinition


PROJECT_ROOT = Path(__file__).resolve().parents[2]
_configured_roots = os.environ.get("SMR_ARTIFACT_ROOTS", "").split(os.pathsep)
DEFAULT_ARTIFACT_ROOT = Path(_configured_roots[0]) if _configured_roots[0] else PROJECT_ROOT / "06_outputs" / "workflows"
Scheduler = Callable[[SchedulerJobRequest], AdapterResult]


def _json(raw: Any) -> dict[str, Any]:
    try:
        return json.loads(raw or "{}") if not isinstance(raw, dict) else raw
    except (TypeError, ValueError):
        return {}


def _validate(context: WorkflowContext) -> StageResult:
    allow_network = context.input_data.get("allow_network", False)
    run_refresh_job = context.input_data.get("run_refresh_job", False)
    if not isinstance(allow_network, bool) or allow_network:
        raise ValueError("portfolio_review only supports allow_network=false")
    if not isinstance(run_refresh_job, bool):
        raise ValueError("run_refresh_job must be a boolean")
    context.state["run_refresh_job"] = run_refresh_job
    return StageResult.completed("Portfolio review input validated")


def _scheduler_stage(scheduler: Scheduler):
    def handler(context: WorkflowContext) -> StageResult:
        request = SchedulerJobRequest("portfolio_review", dry_run=not context.state["run_refresh_job"])
        result = scheduler(request)
        context.state["scheduler"] = result.to_dict()
        return StageResult.completed("Portfolio adapter completed", {"scheduler_status": result.status})

    return handler


def _load_positions(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    if not relation_exists(conn, "paper_portfolio_positions"):
        return []
    rows = conn.execute(
        """
        SELECT position_id, ticker, market, quantity, avg_cost, position_pct, opened_at,
               source_recommendation_id, metadata_json
        FROM paper_portfolio_positions WHERE status='open'
        ORDER BY ticker, position_id
        """
    ).fetchall()
    return [
        {
            "position_id": row[0], "ticker": row[1], "market": row[2], "quantity": row[3],
            "avg_cost": row[4], "position_pct": float(row[5] or 0), "opened_at": row[6],
            "source_recommendation_id": row[7], "metadata": _json(row[8]),
        }
        for row in rows
    ]


def _review(context: WorkflowContext) -> StageResult:
    conn = sqlite3.connect(context.db_path)
    try:
        positions = _load_positions(conn)
        decisions: list[dict[str, Any]] = []
        for ticker in dict.fromkeys(str(item.get("ticker") or "") for item in positions):
            result = load_decision_context(conn, DecisionContextRequest(ticker, limit=20))
            decisions.extend(result.data.get("items") or [])
    finally:
        conn.close()

    by_market: defaultdict[str, float] = defaultdict(float)
    by_theme: defaultdict[str, float] = defaultdict(float)
    for position in positions:
        by_market[str(position.get("market") or "unknown")] += position["position_pct"]
        by_theme[str(position["metadata"].get("theme") or "unknown")] += position["position_pct"]
    risk_flags: list[str] = []
    if any(position["position_pct"] > 20 for position in positions):
        risk_flags.append("single_position_concentration")
    if sum(item["position_pct"] for item in positions) > 100:
        risk_flags.append("total_exposure_over_100")
    tickers = [str(item.get("ticker") or "") for item in positions]
    if any(count > 1 for count in Counter(tickers).values()):
        risk_flags.append("duplicate_open_ticker")
    if positions and len({item["ticker"] for item in decisions}) < len(set(tickers)):
        risk_flags.append("missing_decision_context")
    if any(position["metadata"].get("price_status") in {"stale", "missing"} for position in positions):
        risk_flags.append("stale_or_missing_price")

    summary = {
        "position_count": len(positions), "decision_count": len(decisions),
        "total_exposure_pct": round(sum(item["position_pct"] for item in positions), 4),
        "exposure_by_market": {key: round(value, 4) for key, value in sorted(by_market.items())},
        "exposure_by_theme": {key: round(value, 4) for key, value in sorted(by_theme.items())},
        "positions": positions, "decision_status_counts": dict(Counter(str(item.get("status") or "unknown") for item in decisions)),
        "risk_flags": risk_flags, "scheduler": context.state.get("scheduler"), "allow_network": False,
    }
    context.state["summary"] = summary
    return StageResult.completed("Paper portfolio and decision ledger reviewed", summary)


def _render(summary: dict[str, Any]) -> str:
    lines = [
        "# Paper Portfolio Review", "", f"- Open positions: **{summary['position_count']}**",
        f"- Total exposure: **{summary['total_exposure_pct']}%**", f"- Decision records: **{summary['decision_count']}**", "",
        "## Positions", "", "| Ticker | Market | Exposure | Decision source |", "|---|---:|---:|---|",
    ]
    for item in summary["positions"]:
        lines.append(f"| {item['ticker']} | {item['market']} | {item['position_pct']}% | {item.get('source_recommendation_id') or '—'} |")
    lines.extend(["", "## Risk flags", ""])
    lines.extend([f"- {flag}" for flag in summary["risk_flags"]] or ["- No configured portfolio flag was triggered."])
    lines.extend(["", "This review reads the paper portfolio only and never places orders.", ""])
    return "\n".join(lines)


def _write(artifact_root: Path):
    def handler(context: WorkflowContext) -> StageResult:
        run_dir = artifact_root.resolve() / context.run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        path = run_dir / "portfolio_review.md"
        path.write_text(_render(context.state["summary"]), encoding="utf-8")
        conn = sqlite3.connect(context.db_path)
        try:
            artifact = ArtifactStore(conn, [artifact_root]).register_artifact(
                context.run_id, "portfolio_review", "Paper portfolio review", path, "text/markdown",
                metadata={"position_count": context.state["summary"]["position_count"]},
            )
        finally:
            conn.close()
        summary = {**context.state["summary"], "artifacts": [artifact["artifact_id"]]}
        context.state["summary"] = summary
        return StageResult.completed("Portfolio review persisted", summary, artifacts=(artifact,))

    return handler


def portfolio_review_definition(
    *, artifact_root: str | Path | None = None, scheduler: Scheduler = run_scheduler_job,
) -> WorkflowDefinition:
    root = Path(artifact_root) if artifact_root is not None else DEFAULT_ARTIFACT_ROOT
    return WorkflowDefinition(
        workflow_id="portfolio_review", title="Portfolio review", description="Review paper portfolio risk and decision context.",
        input_schema={
            "type": "object", "properties": {"allow_network": {"type": "boolean", "default": False}, "run_refresh_job": {"type": "boolean", "default": False}},
            "additionalProperties": False,
        },
        stages=(
            StageDefinition("validate_input", _validate),
            StageDefinition("scheduler_adapter", _scheduler_stage(scheduler)),
            StageDefinition("review_portfolio", _review),
            StageDefinition("write_review", _write(root)),
        ),
    )
