from __future__ import annotations

import ast
import json
import math
import sqlite3
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from smr_app.runtime.artifact_store import ArtifactStore
from smr_app.runtime.contracts import StageDefinition, StageResult, WorkflowContext, WorkflowDefinition


DEFAULT_ARTIFACT_ROOT = Path("06_outputs") / "workflows"
ALLOWED_TYPES = {"fact", "assumption", "driver", "model", "output"}
ALLOWED_OPERATORS = {
    ast.Add: lambda a, b: a + b,
    ast.Sub: lambda a, b: a - b,
    ast.Mult: lambda a, b: a * b,
    ast.Div: lambda a, b: a / b,
    ast.Pow: lambda a, b: a**b,
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _evaluate_formula(expression: str, values: dict[str, float]) -> float:
    """Evaluate the deliberately small arithmetic language used by correction claims."""

    def visit(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return visit(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.Name) and node.id in values:
            return float(values[node.id])
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = visit(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp) and type(node.op) in ALLOWED_OPERATORS:
            return float(ALLOWED_OPERATORS[type(node.op)](visit(node.left), visit(node.right)))
        raise ValueError(f"formula contains unsupported syntax: {ast.dump(node, include_attributes=False)}")

    value = visit(ast.parse(expression, mode="eval"))
    if not math.isfinite(value):
        raise ValueError("formula result must be finite")
    return value


def _validate_input(ctx: WorkflowContext) -> StageResult:
    data = ctx.input_data
    claims = data.get("claims")
    correction = data.get("correction")
    if not isinstance(claims, list) or not claims:
        raise ValueError("claims must be a non-empty array")
    if not isinstance(correction, dict):
        raise ValueError("correction must be an object")
    required_correction = {"claim_id", "new_value", "source", "evidence_id"}
    missing = sorted(required_correction - set(correction))
    if missing:
        raise ValueError(f"correction missing required fields: {missing}")
    if not str(correction.get("source") or "").strip() or not str(correction.get("evidence_id") or "").strip():
        raise ValueError("a correction cannot be approved without source and evidence_id")

    normalized: dict[str, dict[str, Any]] = {}
    for raw in claims:
        if not isinstance(raw, dict):
            raise ValueError("each claim must be an object")
        claim_id = str(raw.get("claim_id") or "").strip()
        if not claim_id.isidentifier():
            raise ValueError(f"claim_id must be a formula-safe identifier: {claim_id!r}")
        if claim_id in normalized:
            raise ValueError(f"duplicate claim_id: {claim_id}")
        claim_type = str(raw.get("claim_type") or "")
        if claim_type not in ALLOWED_TYPES:
            raise ValueError(f"invalid claim_type for {claim_id}: {claim_type}")
        upstream = raw.get("upstream_claim_ids") or []
        if not isinstance(upstream, list) or not all(isinstance(item, str) for item in upstream):
            raise ValueError(f"upstream_claim_ids must be string array for {claim_id}")
        normalized[claim_id] = {
            **raw,
            "claim_id": claim_id,
            "claim_type": claim_type,
            "upstream_claim_ids": list(upstream),
            "version": int(raw.get("version") or 1),
        }

    target_id = str(correction["claim_id"])
    if target_id not in normalized:
        raise ValueError(f"correction target does not exist: {target_id}")
    for claim in normalized.values():
        missing_upstream = [item for item in claim["upstream_claim_ids"] if item not in normalized]
        if missing_upstream:
            raise ValueError(f"{claim['claim_id']} has missing upstream claims: {missing_upstream}")
        if claim.get("formula") and not claim["upstream_claim_ids"]:
            raise ValueError(f"computed claim has no upstream dependencies: {claim['claim_id']}")

    ctx.state["claims"] = normalized
    ctx.state["correction"] = dict(correction)
    return StageResult.completed(
        "纠错输入、来源与证据标识已校验",
        {"claim_count": len(normalized), "target_claim_id": target_id},
    )


def _build_dependency_graph(ctx: WorkflowContext) -> StageResult:
    claims = ctx.state["claims"]
    downstream: dict[str, list[str]] = {claim_id: [] for claim_id in claims}
    indegree: dict[str, int] = {claim_id: 0 for claim_id in claims}
    for claim in claims.values():
        for upstream_id in claim["upstream_claim_ids"]:
            downstream[upstream_id].append(claim["claim_id"])
            indegree[claim["claim_id"]] += 1

    queue = deque(sorted(key for key, degree in indegree.items() if degree == 0))
    order: list[str] = []
    while queue:
        claim_id = queue.popleft()
        order.append(claim_id)
        for child in downstream[claim_id]:
            indegree[child] -= 1
            if indegree[child] == 0:
                queue.append(child)
    if len(order) != len(claims):
        raise ValueError("claim dependency graph contains a cycle")

    target_id = ctx.state["correction"]["claim_id"]
    impacted = {target_id}
    walk = deque([target_id])
    while walk:
        current = walk.popleft()
        for child in downstream[current]:
            if child not in impacted:
                impacted.add(child)
                walk.append(child)
    ctx.state.update({"downstream": downstream, "topological_order": order, "impacted_ids": impacted})
    return StageResult.completed(
        "依赖图已构建并完成环路检查",
        {"impacted_claim_count": len(impacted), "topological_order": order},
    )


def _recompute_impacted_claims(ctx: WorkflowContext) -> StageResult:
    claims = ctx.state["claims"]
    correction = ctx.state["correction"]
    target_id = correction["claim_id"]
    impacted = ctx.state["impacted_ids"]
    old_values = {claim_id: claim.get("value") for claim_id, claim in claims.items()}
    new_values = dict(old_values)
    new_values[target_id] = correction["new_value"]

    recomputed_ids: list[str] = []
    for claim_id in ctx.state["topological_order"]:
        if claim_id == target_id or claim_id not in impacted:
            continue
        claim = claims[claim_id]
        formula = str(claim.get("formula") or "").strip()
        if not formula:
            raise ValueError(
                f"impacted downstream claim {claim_id} has no deterministic formula; "
                "the correction is blocked instead of silently preserving a stale value"
            )
        variables = {upstream_id: new_values[upstream_id] for upstream_id in claim["upstream_claim_ids"]}
        if not all(isinstance(value, (int, float)) for value in variables.values()):
            raise ValueError(f"formula inputs for {claim_id} must be numeric")
        new_values[claim_id] = _evaluate_formula(formula, variables)
        recomputed_ids.append(claim_id)

    changes = []
    for claim_id in ctx.state["topological_order"]:
        if claim_id not in impacted:
            continue
        claim = claims[claim_id]
        changes.append(
            {
                "claim_id": claim_id,
                "claim_type": claim["claim_type"],
                "metric": claim.get("metric") or claim_id,
                "unit": claim.get("unit") or "",
                "old_value": old_values[claim_id],
                "new_value": new_values[claim_id],
                "old_version": claim["version"],
                "new_version": claim["version"] + 1,
                "recomputed": claim_id in recomputed_ids,
            }
        )
    ctx.state.update({"old_values": old_values, "new_values": new_values, "changes": changes})
    return StageResult.completed(
        "已按依赖拓扑顺序完成全部下游重算",
        {"changed_claim_count": len(changes), "recomputed_claim_ids": recomputed_ids},
    )


def _quality_gate(ctx: WorkflowContext) -> StageResult:
    target_id = ctx.state["correction"]["claim_id"]
    impacted = ctx.state["impacted_ids"]
    changed_ids = {change["claim_id"] for change in ctx.state["changes"]}
    missing = sorted(impacted - changed_ids)
    stale = [
        change["claim_id"]
        for change in ctx.state["changes"]
        if change["claim_id"] != target_id and not change["recomputed"]
    ]
    checks = {
        "source_present": bool(ctx.state["correction"].get("source")),
        "evidence_present": bool(ctx.state["correction"].get("evidence_id")),
        "all_impacted_claims_covered": not missing,
        "all_downstream_claims_recomputed": not stale,
        "all_numeric_results_finite": all(
            not isinstance(change["new_value"], float) or math.isfinite(change["new_value"])
            for change in ctx.state["changes"]
        ),
    }
    if not all(checks.values()):
        raise ValueError(f"claim correction quality gate failed: {checks}; missing={missing}; stale={stale}")
    ctx.state["quality_checks"] = checks
    return StageResult.completed("纠错质量门通过", {"quality_checks": checks, "approved": True})


def _persist_outputs_stage(artifact_root: Path):
    def handler(ctx: WorkflowContext) -> StageResult:
        root = artifact_root.resolve()
        output_dir = root / ctx.run_id
        output_dir.mkdir(parents=True, exist_ok=True)
        correction = ctx.state["correction"]
        payload = {
            "schema_version": "1.0",
            "workflow_id": "claim_correction",
            "run_id": ctx.run_id,
            "entity_key": ctx.input_data.get("entity_key"),
            "corrected_at": _utc_now(),
            "correction": correction,
            "changes": ctx.state["changes"],
            "quality_checks": ctx.state["quality_checks"],
            "approved": True,
        }
        json_path = output_dir / "correction_diff.json"
        json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

        lines = [
            "# 研究主张纠错记录",
            "",
            f"- 标的：{ctx.input_data.get('entity_key') or '未指定'}",
            f"- 被纠正主张：`{correction['claim_id']}`",
            f"- 纠错依据：{correction['source']} [{correction['evidence_id']}]",
            "- 状态：已通过来源、依赖传播和独立复算质量门",
            "",
            "## 变更与下游重算",
            "",
            "| 主张 | 指标 | 旧值 | 新值 | 单位 | 处理 |",
            "|---|---|---:|---:|---|---|",
        ]
        for change in ctx.state["changes"]:
            action = "下游复算" if change["recomputed"] else "直接纠正"
            lines.append(
                f"| `{change['claim_id']}` | {change['metric']} | {change['old_value']} | "
                f"{change['new_value']} | {change['unit']} | {action} |"
            )
        lines.extend(
            [
                "",
                "## 质量门",
                "",
                *[
                    f"- {name}：{'通过' if passed else '未通过'}"
                    for name, passed in ctx.state["quality_checks"].items()
                ],
                "",
                "> 本制品只记录有证据标识的纠错；任一下游缺少确定性公式时，工作流会阻断而不是保留旧值。",
            ]
        )
        markdown_path = output_dir / "correction_memo.md"
        markdown_path.write_text("\n".join(lines), encoding="utf-8")

        conn = sqlite3.connect(ctx.db_path)
        try:
            store = ArtifactStore(conn, [root])
            diff_artifact = store.register_artifact(
                ctx.run_id,
                "correction_diff",
                "研究主张纠错差异",
                json_path,
                "application/json",
                metadata={"claim_id": correction["claim_id"], "approved": True},
            )
            memo_artifact = store.register_artifact(
                ctx.run_id,
                "claim_correction_report",
                "研究主张纠错记录",
                markdown_path,
                "text/markdown",
                metadata={"claim_id": correction["claim_id"], "approved": True},
            )
            for change in ctx.state["changes"]:
                latest = conn.execute(
                    "SELECT COALESCE(MAX(version), 0) FROM research_claim_versions WHERE claim_id=?",
                    (change["claim_id"],),
                ).fetchone()[0]
                stored_version = max(int(change["new_version"]), int(latest) + 1)
                conn.execute(
                    """
                    INSERT INTO research_claim_versions(
                        claim_id, version, entity_key, claim_type, metric, value_json, unit,
                        source, evidence_id, confidence, status, source_run_id, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1.0, 'active', ?, ?)
                    """,
                    (
                        change["claim_id"],
                        stored_version,
                        ctx.input_data.get("entity_key"),
                        change["claim_type"],
                        change["metric"],
                        json.dumps(change["new_value"], ensure_ascii=False),
                        change["unit"],
                        correction["source"] if change["claim_id"] == correction["claim_id"] else "deterministic recomputation",
                        correction["evidence_id"],
                        ctx.run_id,
                        _utc_now(),
                    ),
                )
            for parent_id, children in ctx.state["downstream"].items():
                for child_id in children:
                    conn.execute(
                        """
                        INSERT OR REPLACE INTO research_claim_dependencies(
                            upstream_claim_id, downstream_claim_id, relation_type, created_at
                        ) VALUES (?, ?, 'depends_on', ?)
                        """,
                        (parent_id, child_id, _utc_now()),
                    )
            conn.execute(
                """
                INSERT INTO research_claim_corrections(
                    correction_id, disputed_claim_id, user_reported_value_json,
                    authoritative_value_json, authoritative_evidence_id, status,
                    impact_json, source_run_id, created_at, completed_at
                ) VALUES (?, ?, ?, ?, ?, 'applied', ?, ?, ?, ?)
                """,
                (
                    f"correction_{ctx.run_id}",
                    correction["claim_id"],
                    json.dumps(ctx.state["old_values"][correction["claim_id"]], ensure_ascii=False),
                    json.dumps(correction["new_value"], ensure_ascii=False),
                    correction["evidence_id"],
                    json.dumps(ctx.state["changes"], ensure_ascii=False),
                    ctx.run_id,
                    _utc_now(),
                    _utc_now(),
                ),
            )
            conn.commit()
        finally:
            conn.close()

        summary = {
            "approved": True,
            "claim_id": correction["claim_id"],
            "changed_claim_count": len(ctx.state["changes"]),
            "changes": ctx.state["changes"],
            "correction": correction,
            "artifact_ids": [diff_artifact["artifact_id"], memo_artifact["artifact_id"]],
            "output_dir": str(output_dir),
        }
        return StageResult.completed(
            "纠错差异、可读报告、主张版本和依赖关系已持久化",
            summary,
            artifacts=(diff_artifact, memo_artifact),
        )

    return handler


def claim_correction_definition(*, artifact_root: str | Path | None = None) -> WorkflowDefinition:
    root = Path(artifact_root) if artifact_root is not None else DEFAULT_ARTIFACT_ROOT
    return WorkflowDefinition(
        workflow_id="claim_correction",
        title="Claim correction",
        description="Correct an evidence-backed claim and deterministically recompute every dependent claim.",
        input_schema={
            "type": "object",
            "required": ["entity_key", "claims", "correction"],
            "properties": {
                "entity_key": {"type": "string"},
                "claims": {"type": "array", "items": {"type": "object"}},
                "correction": {"type": "object"},
                "allow_network": {"type": "boolean", "default": False},
            },
            "additionalProperties": False,
        },
        stages=(
            StageDefinition("validate_input", _validate_input, "校验纠错来源、证据和主张"),
            StageDefinition("build_dependency_graph", _build_dependency_graph, "构建依赖图并检查环路"),
            StageDefinition("recompute_impacted_claims", _recompute_impacted_claims, "传播纠错并重算下游"),
            StageDefinition("quality_gate", _quality_gate, "阻断遗漏重算和无证据纠错"),
            StageDefinition("persist_outputs", _persist_outputs_stage(root), "保存差异、版本和审计制品"),
        ),
    )
