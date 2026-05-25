#!/usr/bin/env python3
"""Recommendation state machine, human review, decision ledger, and agent audit trail."""

from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import asdict
from datetime import datetime
from typing import Any

from smr_data_health import gate_to_dict, new_agent_run_id
from smr_research_quality import quality_to_dict, report_has_action
from smr_wiki import generate_execution_id

RECOMMENDATION_STATUSES = {
    "draft",
    "candidate_shadow",
    "observation_only",
    "blocked_by_data",
    "blocked_by_evidence",
    "blocked_by_lint",
    "pending_human_review",
    "approved_paper",
    "rejected",
    "archived",
    "expired",
}

REVIEW_ACTIONS = {
    "approve_paper",
    "reject",
    "request_more_research",
    "downgrade_to_observation",
    "reduce_position_size",
    "archive",
}


def ensure_decision_tables(conn: sqlite3.Connection) -> None:
    conn.execute("PRAGMA busy_timeout=15000")
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS recommendation_reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            recommendation_id TEXT NOT NULL,
            previous_status TEXT NOT NULL,
            new_status TEXT NOT NULL,
            reviewer TEXT,
            review_action TEXT,
            review_comment TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            metadata_json TEXT NOT NULL DEFAULT '{}'
        );

        CREATE TABLE IF NOT EXISTS decision_ledger (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            decision_id TEXT UNIQUE NOT NULL,
            recommendation_id TEXT NOT NULL,
            ticker TEXT,
            market TEXT,
            theme TEXT,
            action TEXT NOT NULL,
            status TEXT NOT NULL,
            decision_time TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            reference_price REAL,
            currency TEXT,
            suggested_position_pct REAL,
            max_position_pct REAL,
            thesis_summary TEXT,
            evidence_ids_json TEXT NOT NULL DEFAULT '[]',
            bear_case_summary TEXT,
            kill_conditions_json TEXT NOT NULL DEFAULT '[]',
            risk_notes TEXT,
            data_health_snapshot_json TEXT NOT NULL DEFAULT '{}',
            evidence_check_snapshot_json TEXT NOT NULL DEFAULT '{}',
            lint_snapshot_json TEXT NOT NULL DEFAULT '{}',
            risk_snapshot_json TEXT NOT NULL DEFAULT '{}',
            human_review_status TEXT,
            reviewer TEXT,
            review_comment TEXT,
            outcome_status TEXT NOT NULL DEFAULT 'open',
            outcome_price_1d REAL,
            outcome_price_1w REAL,
            outcome_price_1m REAL,
            outcome_price_3m REAL,
            thesis_confirmed INTEGER,
            failure_reason TEXT,
            metadata_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_decision_ledger_recommendation
        ON decision_ledger(recommendation_id, updated_at DESC);

        CREATE INDEX IF NOT EXISTS idx_recommendation_reviews_rec
        ON recommendation_reviews(recommendation_id, created_at DESC);

        CREATE TABLE IF NOT EXISTS agent_runs (
            run_id TEXT PRIMARY KEY,
            agent_or_script TEXT NOT NULL,
            entity_type TEXT,
            entity_id TEXT,
            status TEXT NOT NULL,
            started_at TEXT,
            completed_at TEXT,
            data_health_snapshot_json TEXT NOT NULL DEFAULT '{}',
            freshness_gate_result_json TEXT NOT NULL DEFAULT '{}',
            evidence_check_result_json TEXT NOT NULL DEFAULT '{}',
            lint_result_json TEXT NOT NULL DEFAULT '{}',
            source_registry_snapshot_json TEXT NOT NULL DEFAULT '{}',
            output_status TEXT,
            block_reasons_json TEXT NOT NULL DEFAULT '[]',
            metadata_json TEXT NOT NULL DEFAULT '{}',
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    columns = {row[1] for row in conn.execute("PRAGMA table_info(decision_ledger)").fetchall()}
    if "performance_update_status" not in columns:
        conn.execute("ALTER TABLE decision_ledger ADD COLUMN performance_update_status TEXT")
    if "performance_update_reason" not in columns:
        conn.execute("ALTER TABLE decision_ledger ADD COLUMN performance_update_reason TEXT")


def dumps(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, sort_keys=True, default=str)


def loads(raw: str | None, fallback: Any) -> Any:
    if raw in (None, ""):
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def merge_metadata(existing: dict[str, Any], updates: dict[str, Any]) -> dict[str, Any]:
    """Preserve durable lifecycle traces while refreshing volatile snapshots."""
    merged = {**existing, **updates}
    if existing.get("paper_portfolio") and not updates.get("paper_portfolio"):
        merged["paper_portfolio"] = existing["paper_portfolio"]
    if existing.get("review_overrides") and not updates.get("review_overrides"):
        merged["review_overrides"] = existing["review_overrides"]
    return merged


def _as_dict(value: Any) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _field_names(items: Any) -> list[str]:
    fields: list[str] = []
    for item in items or []:
        if isinstance(item, dict):
            field = item.get("field") or item.get("code")
        else:
            field = item
        if field is not None and str(field).strip():
            fields.append(str(field))
    return list(dict.fromkeys(fields))


def _gate_from_metadata(metadata: dict[str, Any], key: str) -> dict[str, Any]:
    direct = metadata.get(key)
    if isinstance(direct, dict):
        return direct
    promotion = _as_dict(metadata.get("promotion_result"))
    snapshots = _as_dict(promotion.get("snapshots"))
    gate = snapshots.get(key)
    return gate if isinstance(gate, dict) else {}


def _audit_status_from_gate(gate: Any) -> str | None:
    if isinstance(gate, dict):
        return gate.get("status") or gate.get("after_status") or gate.get("overall_status")
    if gate:
        return str(gate)
    return None


def build_review_audit_metadata(
    metadata: dict[str, Any] | None,
    *,
    status: str | None = None,
    dashboard_summary: dict[str, Any] | None = None,
    risk_snapshot: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize Phase 14 review/ledger audit fields.

    This helper is intentionally additive. It does not grant approval, create
    paper orders, or change promotion outcomes.
    """

    metadata = dict(metadata or {})
    dashboard_summary = dashboard_summary or {}
    risk_snapshot = risk_snapshot or {}
    promotion = _as_dict(metadata.get("promotion_result"))
    snapshots = _as_dict(promotion.get("snapshots"))
    candidate = _as_dict(metadata.get("candidate"))
    thesis_inference = _as_dict(metadata.get("thesis_inference") or snapshots.get("thesis_inference"))
    field_gate = _gate_from_metadata(metadata, "promotion_evidence_gate")
    data_quality_gate = _gate_from_metadata(metadata, "data_quality_gate")
    bear_case_gate = _gate_from_metadata(metadata, "bear_case_gate")
    consensus_proxy = _as_dict(metadata.get("consensus_proxy") or snapshots.get("consensus_proxy"))

    thesis_types = (
        metadata.get("thesis_types")
        or snapshots.get("thesis_types")
        or field_gate.get("thesis_types")
        or []
    )
    primary_thesis = (
        metadata.get("primary_thesis_type")
        or thesis_inference.get("primary_thesis_type")
        or (thesis_types[0] if isinstance(thesis_types, list) and thesis_types else None)
        or "unknown"
    )
    promotion_mode = metadata.get("promotion_mode") or candidate.get("promotion_mode") or snapshots.get("promotion_mode")
    position_policy = metadata.get("position_policy") or candidate.get("position_policy") or snapshots.get("position_policy")
    if field_gate:
        core_blockers = _field_names(field_gate.get("core_blockers"))
        supporting_warnings = _field_names(field_gate.get("supporting_warnings"))
        optional_warnings = _field_names(field_gate.get("optional_warnings"))
    else:
        core_blockers = _field_names(metadata.get("core_blockers"))
        supporting_warnings = _field_names(metadata.get("supporting_warnings"))
        optional_warnings = _field_names(metadata.get("optional_warnings"))
    data_quality_status = metadata.get("data_quality_gate_status") or _audit_status_from_gate(data_quality_gate)
    bear_case_status = metadata.get("bear_case_status") or _audit_status_from_gate(bear_case_gate)
    residual_risk_level = metadata.get("residual_risk_level") or bear_case_gate.get("residual_risk_level")
    reduced_size_pending = promotion_mode == "reduced_size_pending" or position_policy == "reduced_size"
    pending_review = status == "pending_human_review" or str(metadata.get("status") or "") == "pending_human_review"
    audit_flags = list(metadata.get("audit_flags") or [])

    if pending_review:
        audit_flags.append("requires_human_review")
    if reduced_size_pending:
        audit_flags.extend(["reduced_size_only", "requires_human_review"])
    if optional_warnings:
        audit_flags.append("optional_missing_fields_present")
    if consensus_proxy and not bool(consensus_proxy.get("is_official_consensus") or consensus_proxy.get("official_consensus_active")):
        audit_flags.append("proxy_eps_not_official_consensus")

    audit_updates = {
        "primary_thesis_type": primary_thesis,
        "thesis_inference_confidence": metadata.get("thesis_inference_confidence")
        if metadata.get("thesis_inference_confidence") is not None
        else thesis_inference.get("confidence"),
        "promotion_mode": promotion_mode,
        "position_policy": position_policy,
        "core_blockers": core_blockers,
        "supporting_warnings": supporting_warnings,
        "optional_warnings": optional_warnings,
        "data_quality_gate_status": data_quality_status,
        "bear_case_status": bear_case_status,
        "residual_risk_level": residual_risk_level,
        "requires_human_review": bool(pending_review or reduced_size_pending or metadata.get("requires_human_review")),
        "auto_approval_allowed": False if pending_review or reduced_size_pending else bool(metadata.get("auto_approval_allowed", False)),
        "paper_order_allowed": bool(status == "approved_paper" and metadata.get("paper_order_allowed")),
        "audit_flags": list(dict.fromkeys(str(item) for item in audit_flags if str(item).strip())),
    }
    if thesis_inference:
        audit_updates["thesis_inference"] = thesis_inference
    if data_quality_status is not None:
        if isinstance(metadata.get("data_quality_gate"), dict):
            audit_updates["data_quality_gate_detail"] = metadata.get("data_quality_gate")
        audit_updates["data_quality_gate"] = data_quality_status
    if bear_case_gate:
        audit_updates["bear_case_gate"] = bear_case_gate
    if risk_snapshot and "portfolio_risk_status" not in metadata:
        audit_updates["portfolio_risk_status"] = risk_snapshot.get("status") or risk_snapshot.get("risk_status")
    return {**metadata, **audit_updates}


def review_audit_detail_from_metadata(
    recommendation_id: str,
    metadata: dict[str, Any] | None,
    *,
    status: str | None = None,
    ticker: str | None = None,
) -> dict[str, Any]:
    """Build a review-detail friendly view of thesis-aware audit metadata."""

    metadata = build_review_audit_metadata(metadata, status=status)
    candidate = _as_dict(metadata.get("candidate"))
    bear_case_gate = _as_dict(metadata.get("bear_case_gate"))
    return {
        "recommendation_id": recommendation_id,
        "ticker": ticker or metadata.get("ticker") or candidate.get("ticker"),
        "status": status,
        "promotion_mode": metadata.get("promotion_mode"),
        "position_policy": metadata.get("position_policy"),
        "suggested_position_pct": candidate.get("suggested_position_pct") or metadata.get("suggested_position_pct"),
        "primary_thesis_type": metadata.get("primary_thesis_type"),
        "field_gate": {
            "core_blockers": metadata.get("core_blockers") or [],
            "supporting_warnings": metadata.get("supporting_warnings") or [],
            "optional_warnings": metadata.get("optional_warnings") or [],
        },
        "bear_case_gate": {
            "overall_status": bear_case_gate.get("overall_status") or metadata.get("bear_case_status"),
            "residual_risk_level": bear_case_gate.get("residual_risk_level") or metadata.get("residual_risk_level"),
            "action_effect": bear_case_gate.get("action_effect"),
        },
        "portfolio_risk_status": metadata.get("portfolio_risk_status"),
        "requires_human_review": bool(metadata.get("requires_human_review")),
        "auto_approval_allowed": bool(metadata.get("auto_approval_allowed")),
        "paper_order_allowed": bool(metadata.get("paper_order_allowed")),
        "audit_flags": metadata.get("audit_flags") or [],
    }


def update_decision_ledger_metadata(
    conn: sqlite3.Connection,
    recommendation_id: str,
    metadata_updates: dict[str, Any],
    *,
    status: str | None = None,
) -> dict[str, Any]:
    """Merge metadata into a decision ledger row and re-run audit normalization."""

    ensure_decision_tables(conn)
    row = conn.execute(
        """
        SELECT status, metadata_json
        FROM decision_ledger
        WHERE recommendation_id=?
        ORDER BY datetime(updated_at) DESC, id DESC
        LIMIT 1
        """,
        (recommendation_id,),
    ).fetchone()
    if not row:
        return {}
    current_status = status or row[0]
    metadata = merge_metadata(loads(row[1], {}), metadata_updates or {})
    metadata = build_review_audit_metadata(metadata, status=current_status)
    conn.execute(
        """
        UPDATE decision_ledger
        SET metadata_json=?, updated_at=?
        WHERE recommendation_id=?
        """,
        (dumps(metadata), datetime.now().strftime("%Y-%m-%d %H:%M:%S"), recommendation_id),
    )
    return {"recommendation_id": recommendation_id, "status": current_status, "metadata": metadata}


def parse_action(summary: dict[str, Any] | None, fallback: str = "") -> str:
    summary = summary or {}
    action = str(summary.get("action_detail") or summary.get("action") or fallback or "").strip()
    return action or "observation"


def parse_primary_ticker(action_text: str | None) -> tuple[str | None, str | None]:
    text = str(action_text or "")
    match = re.search(r"([0-9]{6}\.(?:SZ|SH|BJ)|[0-9]{5}\.HK|[A-Z]{1,6})", text)
    if not match:
        return None, None
    ticker = match.group(1)
    if ticker.endswith(".SZ") or ticker.endswith(".SH") or ticker.endswith(".BJ"):
        return ticker, "A"
    if ticker.endswith(".HK"):
        return ticker, "H"
    return ticker, "US"


def determine_recommendation_status(
    dashboard_summary: dict[str, Any] | None,
    freshness_gate_result: Any,
    evidence_check_result: Any,
    lint_result: Any,
) -> tuple[str, list[str]]:
    gate = gate_to_dict(freshness_gate_result)
    evidence = quality_to_dict(evidence_check_result)
    lint = quality_to_dict(lint_result)
    reasons: list[str] = []
    action = report_has_action("", dashboard_summary)

    if gate.get("status") == "block":
        reasons.extend(gate.get("reasons") or ["Freshness Gate block"])
        return "blocked_by_data", reasons
    if evidence.get("severity") == "block" or (action and evidence.get("recommendation_allowed") is False):
        reasons.extend(evidence.get("reasons") or ["Evidence checker block"])
        return "blocked_by_evidence", reasons
    if lint.get("max_severity") == "blocker" or lint.get("allowed_publish_status") == "blocked":
        reasons.extend([item.get("message") for item in lint.get("issues") or [] if item.get("message")])
        return "blocked_by_lint", reasons
    if gate.get("status") == "degrade":
        reasons.extend(gate.get("reasons") or ["Freshness Gate degrade"])
        return "observation_only", reasons
    if action:
        return "pending_human_review", reasons
    return "candidate_shadow", reasons


def decision_id_for(recommendation_id: str) -> str:
    return f"decision__{recommendation_id}"


def upsert_decision_ledger(
    conn: sqlite3.Connection,
    recommendation_id: str,
    status: str,
    dashboard_summary: dict[str, Any] | None = None,
    data_health_snapshot: dict[str, Any] | None = None,
    evidence_check_snapshot: dict[str, Any] | None = None,
    lint_snapshot: dict[str, Any] | None = None,
    risk_snapshot: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    reviewer: str | None = None,
    review_comment: str | None = None,
) -> dict[str, Any]:
    ensure_decision_tables(conn)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    summary = dashboard_summary or {}
    action = parse_action(summary)
    data_health = data_health_snapshot or {}
    evidence = evidence_check_snapshot or {}
    lint = lint_snapshot or {}
    risk = risk_snapshot or {}
    metadata = metadata or {}
    previous_row = conn.execute(
        "SELECT status, metadata_json FROM decision_ledger WHERE recommendation_id=? ORDER BY datetime(updated_at) DESC, id DESC LIMIT 1",
        (recommendation_id,),
    ).fetchone()
    previous_status = previous_row[0] if previous_row else None
    previous_metadata = loads(previous_row[1], {}) if previous_row else {}
    metadata = merge_metadata(previous_metadata, metadata)
    metadata = build_review_audit_metadata(
        metadata,
        status=status,
        dashboard_summary=summary,
        risk_snapshot=risk,
    )
    ticker = metadata.get("ticker")
    market = metadata.get("market")
    if not ticker:
        ticker, market = parse_primary_ticker(action)
    gate_status = (((data_health.get("items") or [{}])[0] if isinstance(data_health.get("items"), list) and data_health.get("items") else {}) or {}).get("freshness_status")
    reference_price = None
    if data_health.get("overall_status") in {"fresh", "warn"} and metadata.get("reference_price") is not None:
        reference_price = metadata.get("reference_price")
    decision_id = decision_id_for(recommendation_id)
    conn.execute(
        """
        INSERT INTO decision_ledger (
            decision_id, recommendation_id, ticker, market, theme, action, status, decision_time,
            reference_price, currency, suggested_position_pct, max_position_pct, thesis_summary,
            evidence_ids_json, bear_case_summary, kill_conditions_json, risk_notes,
            data_health_snapshot_json, evidence_check_snapshot_json, lint_snapshot_json, risk_snapshot_json,
            human_review_status, reviewer, review_comment, metadata_json, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(decision_id) DO UPDATE SET
            ticker=excluded.ticker,
            market=excluded.market,
            theme=excluded.theme,
            action=excluded.action,
            status=excluded.status,
            reference_price=excluded.reference_price,
            currency=excluded.currency,
            suggested_position_pct=excluded.suggested_position_pct,
            max_position_pct=excluded.max_position_pct,
            thesis_summary=excluded.thesis_summary,
            evidence_ids_json=excluded.evidence_ids_json,
            bear_case_summary=excluded.bear_case_summary,
            kill_conditions_json=excluded.kill_conditions_json,
            risk_notes=excluded.risk_notes,
            data_health_snapshot_json=excluded.data_health_snapshot_json,
            evidence_check_snapshot_json=excluded.evidence_check_snapshot_json,
            lint_snapshot_json=excluded.lint_snapshot_json,
            risk_snapshot_json=excluded.risk_snapshot_json,
            human_review_status=excluded.human_review_status,
            reviewer=COALESCE(excluded.reviewer, decision_ledger.reviewer),
            review_comment=COALESCE(excluded.review_comment, decision_ledger.review_comment),
            metadata_json=excluded.metadata_json,
            updated_at=excluded.updated_at
        """,
        (
            decision_id,
            recommendation_id,
            ticker,
            market,
            summary.get("theme") or metadata.get("theme"),
            action,
            status,
            now,
            reference_price,
            summary.get("currency") or "CNY",
            summary.get("suggested_position_pct"),
            summary.get("max_position_pct"),
            summary.get("confidence_rationale") or summary.get("primary_signal") or summary.get("action_detail"),
            dumps(summary.get("evidence_ids") or metadata.get("evidence_ids") or []),
            summary.get("bear_case_summary") or metadata.get("bear_case_summary"),
            dumps(summary.get("kill_triggers") or []),
            summary.get("risk_notes") or metadata.get("risk_notes"),
            dumps(data_health),
            dumps(evidence),
            dumps(lint),
            dumps(risk),
            status if status in {"pending_human_review", "approved_paper", "rejected"} else None,
            reviewer,
            review_comment,
            dumps({**metadata, "first_data_health_status": gate_status}),
            now,
            now,
        ),
    )
    return {"decision_id": decision_id, "recommendation_id": recommendation_id, "status": status}


def submit_for_human_review(conn: sqlite3.Connection, recommendation_id: str) -> dict[str, Any]:
    return review_recommendation(
        conn,
        recommendation_id=recommendation_id,
        reviewer=None,
        action="request_more_research",
        comment="系统提交人工审核。",
        overrides={"new_status": "pending_human_review"},
    )


def current_decision_status(conn: sqlite3.Connection, recommendation_id: str) -> str:
    ensure_decision_tables(conn)
    row = conn.execute(
        "SELECT status FROM decision_ledger WHERE recommendation_id=? ORDER BY updated_at DESC LIMIT 1",
        (recommendation_id,),
    ).fetchone()
    return row[0] if row else "candidate_shadow"


def review_recommendation(
    conn: sqlite3.Connection,
    recommendation_id: str,
    reviewer: str | None,
    action: str,
    comment: str | None = None,
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ensure_decision_tables(conn)
    if action not in REVIEW_ACTIONS and action != "request_more_research":
        raise ValueError(f"Unsupported review action: {action}")
    overrides = overrides or {}
    if not str(comment or "").strip():
        raise ValueError("review comment is required")
    previous_status = current_decision_status(conn, recommendation_id)
    if action == "approve_paper" and previous_status.startswith("blocked"):
        raise ValueError("blocked recommendations cannot be approved; archive or request more research")
    if action == "reduce_position_size" and not (
        overrides.get("suggested_position_pct") is not None or overrides.get("new_position_pct") is not None
    ):
        raise ValueError("reduce_position_size requires suggested_position_pct or new_position_pct override")
    mapping = {
        "approve_paper": "approved_paper",
        "reject": "rejected",
        "request_more_research": "pending_human_review",
        "downgrade_to_observation": "observation_only",
        "reduce_position_size": "pending_human_review",
        "archive": "archived",
    }
    new_status = overrides.get("new_status") or mapping[action]
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn.execute(
        """
        INSERT INTO recommendation_reviews (
            recommendation_id, previous_status, new_status, reviewer, review_action, review_comment, created_at, metadata_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            recommendation_id,
            previous_status,
            new_status,
            reviewer,
            action,
            comment,
            now,
            dumps(overrides),
        ),
    )
    row = conn.execute(
        """
        SELECT metadata_json
        FROM decision_ledger
        WHERE recommendation_id=?
        ORDER BY updated_at DESC
        LIMIT 1
        """,
        (recommendation_id,),
    ).fetchone()
    metadata = {}
    if row and row[0]:
        try:
            metadata = json.loads(row[0] or "{}")
        except json.JSONDecodeError:
            metadata = {}
    metadata["review_overrides"] = overrides
    if action == "reduce_position_size":
        metadata["human_review_position_override"] = {
            "reviewer": reviewer,
            "comment": comment,
            "overrides": overrides,
        }
    conn.execute(
        """
        UPDATE decision_ledger
        SET status=?, human_review_status=?, reviewer=?, review_comment=?, metadata_json=?, updated_at=?
        WHERE recommendation_id=?
        """,
        (new_status, new_status, reviewer, comment, dumps(metadata), now, recommendation_id),
    )
    return {
        "recommendation_id": recommendation_id,
        "previous_status": previous_status,
        "new_status": new_status,
        "reviewer": reviewer,
        "review_action": action,
        "review_comment": comment,
    }


def record_agent_run(
    conn: sqlite3.Connection,
    agent_or_script: str,
    status: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    run_id: str | None = None,
    data_health_snapshot: dict[str, Any] | None = None,
    freshness_gate_result: dict[str, Any] | None = None,
    evidence_check_result: dict[str, Any] | None = None,
    lint_result: dict[str, Any] | None = None,
    source_registry_snapshot: dict[str, Any] | None = None,
    output_status: str | None = None,
    block_reasons: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ensure_decision_tables(conn)
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    run_id = run_id or new_agent_run_id("agent_run")
    conn.execute(
        """
        INSERT OR REPLACE INTO agent_runs (
            run_id, agent_or_script, entity_type, entity_id, status, started_at, completed_at,
            data_health_snapshot_json, freshness_gate_result_json, evidence_check_result_json,
            lint_result_json, source_registry_snapshot_json, output_status, block_reasons_json,
            metadata_json, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            run_id,
            agent_or_script,
            entity_type,
            entity_id,
            status,
            (metadata or {}).get("started_at"),
            now,
            dumps(data_health_snapshot or {}),
            dumps(freshness_gate_result or {}),
            dumps(evidence_check_result or {}),
            dumps(lint_result or {}),
            dumps(source_registry_snapshot or {}),
            output_status,
            dumps(block_reasons or []),
            dumps(metadata or {}),
            now,
        ),
    )
    return {"run_id": run_id, "status": status, "output_status": output_status}
