from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

from smr_app.adapters.memory import ALLOWED_RELATIONS, create_memory_candidate, current_approved
from smr_app.runtime.artifact_store import ArtifactStore
from smr_app.runtime.contracts import StageDefinition, StageResult, WorkflowContext, WorkflowDefinition
from smr_app.workflows.stock_deep_dive import parse_ticker


PROJECT_ROOT = Path(__file__).resolve().parents[2]
_configured_roots = os.environ.get("SMR_ARTIFACT_ROOTS", "").split(os.pathsep)
DEFAULT_ARTIFACT_ROOT = Path(_configured_roots[0]) if _configured_roots[0] else PROJECT_ROOT / "06_outputs" / "workflows"


def _validate(context: WorkflowContext) -> StageResult:
    ticker, market = parse_ticker(context.input_data.get("ticker"))
    if context.input_data.get("allow_network", False) is not False:
        raise ValueError("thesis_update only supports allow_network=false")
    updates = context.input_data.get("updates")
    links = context.input_data.get("evidence_links")
    if not isinstance(updates, dict) or not updates:
        raise ValueError("updates must be a non-empty object")
    if not isinstance(links, list) or not links:
        raise ValueError("at least one evidence link is required")
    normalized_links = []
    for link in links:
        if not isinstance(link, dict):
            raise ValueError("evidence links must be objects")
        evidence_id = str(link.get("evidence_id") or "").strip()
        relation = str(link.get("relation") or "supports").strip()
        if not evidence_id or relation not in ALLOWED_RELATIONS:
            raise ValueError("invalid evidence link")
        normalized_links.append({"evidence_id": evidence_id, "relation": relation})
    confidence = context.input_data.get("confidence")
    if confidence is not None and (not isinstance(confidence, (int, float)) or not 0 <= float(confidence) <= 1):
        raise ValueError("confidence must be between 0 and 1")
    context.state.update({"ticker": ticker, "market": market, "updates": updates, "evidence_links": normalized_links, "confidence": confidence})
    return StageResult.completed("Thesis update input validated", {"ticker": ticker, "evidence_count": len(normalized_links)})


def _render(candidate: dict[str, Any]) -> str:
    lines = [
        f"# Thesis Update Proposal — {candidate['entity_id']}", "", f"- Candidate: `{candidate['memory_id']}`",
        f"- Version: **{candidate['version']}**", f"- Parent: `{candidate.get('parent_memory_id') or 'none'}`", "",
        "## Field changes", "",
    ]
    for item in candidate["field_diff"]:
        lines.extend([f"### {item['field']}", "", f"- Before: `{item.get('before')}`", f"- After: `{item.get('after')}`", ""])
    lines.extend(["## Evidence relations", ""])
    lines.extend([f"- [{item['relation']}] `{item['evidence_id']}`" for item in candidate["evidence_links"]])
    lines.extend(["", "This candidate is not active until a human review approves it.", ""])
    return "\n".join(lines)


def _propose(artifact_root: Path):
    def handler(context: WorkflowContext) -> StageResult:
        conn = sqlite3.connect(context.db_path)
        try:
            approved = current_approved(conn, "ticker", context.state["ticker"], "investment_thesis")
            content = {**(approved["content"] if approved else {}), **context.state["updates"]}
            candidate = create_memory_candidate(
                conn, entity_type="ticker", entity_id=context.state["ticker"], memory_type="investment_thesis",
                content=content, evidence_links=context.state["evidence_links"], source_run_id=context.run_id,
                confidence=float(context.state["confidence"]) if context.state["confidence"] is not None else None,
            )
            run_dir = artifact_root.resolve() / context.run_id
            run_dir.mkdir(parents=True, exist_ok=True)
            path = run_dir / "thesis_update.md"
            path.write_text(_render(candidate), encoding="utf-8")
            artifact = ArtifactStore(conn, [artifact_root]).register_artifact(
                context.run_id, "thesis_update_proposal", f"Thesis update — {context.state['ticker']}",
                path, "text/markdown", metadata={"memory_candidate_id": candidate["memory_id"]},
            )
        finally:
            conn.close()
        summary = {
            "ticker": context.state["ticker"], "memory_candidate_id": candidate["memory_id"],
            "parent_memory_id": candidate["parent_memory_id"], "version": candidate["version"],
            "review_status": "candidate", "field_diff": candidate["field_diff"],
            "evidence_ids": [item["evidence_id"] for item in candidate["evidence_links"]],
            "evidence_links": candidate["evidence_links"], "artifact_ids": [artifact["artifact_id"]],
        }
        context.state["summary"] = summary
        return StageResult.completed("Governed thesis candidate created", summary, artifacts=(artifact,))

    return handler


def _await_review(context: WorkflowContext) -> StageResult:
    return StageResult.waiting_review(
        "Human review required before thesis activation", context.state["summary"],
        {"memory_candidate_id": context.state["summary"]["memory_candidate_id"]},
    )


def thesis_update_definition(*, artifact_root: str | Path | None = None) -> WorkflowDefinition:
    root = Path(artifact_root) if artifact_root is not None else DEFAULT_ARTIFACT_ROOT
    return WorkflowDefinition(
        workflow_id="thesis_update", title="Thesis update", description="Propose a governed, evidence-linked thesis version.",
        input_schema={
            "type": "object", "required": ["ticker", "updates", "evidence_links"],
            "properties": {
                "ticker": {"type": "string"}, "updates": {"type": "object"}, "evidence_links": {"type": "array"},
                "confidence": {"type": "number", "minimum": 0, "maximum": 1}, "allow_network": {"type": "boolean", "default": False},
            }, "additionalProperties": False,
        },
        stages=(
            StageDefinition("validate_input", _validate),
            StageDefinition("create_candidate", _propose(root)),
            StageDefinition("await_review", _await_review),
        ),
    )
