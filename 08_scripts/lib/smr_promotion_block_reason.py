#!/usr/bin/env python3
"""Promotion block reason hierarchy for Phase 19 diagnostics."""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from typing import Any

from smr_evidence_quality import build_evidence_quality_gate
from smr_filing_freshness import build_filing_freshness, normalize_ticker
from smr_fundamentals import latest_fundamentals_snapshot
from smr_phase6_watchlists import load_watchlist_config
from smr_recovered_fundamentals import field_recovered_in_snapshot
from smr_wiki import now_ts


BLOCKING_GATES = [
    "DATA_FRESHNESS_GATE",
    "FILING_FRESHNESS_GATE",
    "EVIDENCE_QUALITY_GATE",
    "CORE_EVIDENCE_GATE",
    "NON_CORE_WARNING_GATE",
    "THESIS_CONFIDENCE_GATE",
    "VALUATION_GATE",
    "PROXY_SIGNAL_GATE",
    "BEAR_CASE_GATE",
    "PORTFOLIO_RISK_GATE",
    "REVIEW_STATE_GATE",
    "UNKNOWN_GATE",
]


def loads_json(raw: str | None, fallback: Any) -> Any:
    if raw in (None, ""):
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def relation_exists(conn: sqlite3.Connection, name: str) -> bool:
    row = conn.execute("SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name=?", (name,)).fetchone()
    return bool(row)


def latest_registry_payload(conn: sqlite3.Connection, entity_type: str, entity_id: str | None = None) -> dict[str, Any]:
    if not relation_exists(conn, "task_registry_entry"):
        return {}
    params: list[Any] = [entity_type]
    where = "entity_type=?"
    if entity_id is not None:
        where += " AND entity_id=?"
        params.append(entity_id)
    row = conn.execute(
        f"""
        SELECT payload_json
        FROM task_registry_entry
        WHERE {where}
        ORDER BY datetime(created_at) DESC, snapshot_index DESC, id DESC
        LIMIT 1
        """,
        tuple(params),
    ).fetchone()
    return loads_json(row[0], {}) if row else {}


def latest_phase14_validation(conn: sqlite3.Connection, watchlist_id: str = "ai_core") -> dict[str, Any]:
    return latest_registry_payload(conn, "phase14_thesis_aware_multi_ticker_live_validation", watchlist_id)


def latest_phase18_validation(conn: sqlite3.Connection) -> dict[str, Any]:
    return latest_registry_payload(conn, "phase18_fundamentals_recovery_revalidation", "latest")


def latest_phase6_validation(conn: sqlite3.Connection) -> dict[str, Any]:
    return latest_registry_payload(conn, "phase6_multi_ticker_live_validation", "latest")


def row_for_ticker(payload: dict[str, Any], ticker: str, keys: tuple[str, ...] = ("tickers", "ticker_results")) -> dict[str, Any]:
    ticker = normalize_ticker(ticker)
    for key in keys:
        for row in payload.get(key) or []:
            if normalize_ticker(row.get("ticker")) == ticker:
                return row
    return {}


def parse_tickers(raw: str | None = None, *, watchlist_id: str | None = None) -> list[str]:
    if raw:
        return [normalize_ticker(item) for item in str(raw).split(",") if str(item).strip()]
    if watchlist_id:
        config = load_watchlist_config(watchlist_id)
        return [normalize_ticker(item.get("ticker")) for item in config.get("tickers") or [] if item.get("ticker")]
    return []


def _field_names(items: Any) -> list[str]:
    names = []
    for item in items or []:
        if isinstance(item, dict):
            value = item.get("field") or item.get("code")
        else:
            value = item
        if value:
            names.append(str(value).split(":", 1)[-1])
    return sorted(set(names))


def recovered_fields_for_ticker(conn: sqlite3.Connection, ticker: str) -> list[str]:
    snapshot = latest_fundamentals_snapshot(conn, ticker) or {}
    metadata = snapshot.get("metadata") or {}
    recovered = [str(item.get("field")) for item in metadata.get("phase18_recovered_fields") or [] if item.get("field")]
    for field, detail in (snapshot.get("field_details") or {}).items():
        if detail.get("phase18_recovered") and field_recovered_in_snapshot(field, snapshot):
            recovered.append(str(field))
    return sorted(set(recovered))


def _json_text(value: Any) -> str:
    try:
        return json.dumps(value or {}, ensure_ascii=False, default=str).lower()
    except TypeError:
        return str(value or "").lower()


def _phase6_missing_requirements(phase6_row: dict[str, Any]) -> list[str]:
    values = []
    for key in ("missing_requirements", "blocking_requirements", "promotion_missing_requirements"):
        values.extend([str(item) for item in phase6_row.get(key) or []])
    text = _json_text(phase6_row)
    known = [
        "relevant_filings_not_stale",
        "two_independent_evidence_sources",
        "primary_evidence_for_fundamental_claims",
        "all_core_claims_supported",
        "core_claim_evidence_quality",
        "fresh_valuation_price",
        "consensus_proxy_quality",
        "data_quality_risk_not_high",
        "high_bear_case_unresolved",
        "high_bear_case_partially_mitigated",
    ]
    values.extend(item for item in known if item in text)
    return sorted(set(values))


def _bear_case_gate(row: dict[str, Any], phase6_row: dict[str, Any]) -> dict[str, Any]:
    gate = row.get("bear_case_gate") or {}
    if gate:
        return gate
    response = phase6_row.get("bear_case_response") or {}
    return response.get("bear_case_gate") or {
        "overall_status": response.get("overall_response_status"),
        "residual_risk_level": response.get("residual_risk_level"),
        "action_effect": response.get("action_effect"),
    }


def _valuation_gate_active(phase6_row: dict[str, Any]) -> bool:
    text = _json_text(phase6_row)
    return any(token in text for token in ("fresh_valuation_price", "valuation", "context_only", "blocked_due_to_stale_price"))


def _proxy_gate_active(phase6_row: dict[str, Any]) -> bool:
    text = _json_text(phase6_row)
    return any(token in text for token in ("consensus_proxy_quality", "proxy_quality", "proxy invalid", '"proxy_quality": "invalid"', '"proxy_quality": "weak"'))


def _data_freshness_gate_active(phase6_row: dict[str, Any]) -> bool:
    text = _json_text(phase6_row)
    return any(token in text for token in ("daily_bar", "data freshness", "source stale", "data_health"))


def _why_not_pending(primary: str, recovered: list[str], core_blockers: list[str]) -> str:
    if primary == "REVIEW_STATE_GATE":
        return "ticker is already in the human-review boundary, so Phase 19 keeps audit visibility without auto approval"
    if primary == "THESIS_CONFIDENCE_GATE":
        return "thesis inference is unknown or evidence is metadata-only, so pending review remains disabled"
    if primary == "FILING_FRESHNESS_GATE":
        return "core blockers are resolved, but filing freshness is stale, missing, or not clear enough for promotion"
    if primary == "BEAR_CASE_GATE":
        return "core fundamentals blockers are resolved, but bear case residual risk still blocks or limits promotion"
    if primary == "EVIDENCE_QUALITY_GATE":
        return "core fields may be present, but evidence quality is not strong enough for promotion"
    if primary == "VALUATION_GATE":
        return "fundamentals recovery improved the candidate, but valuation support is still insufficient or stale"
    if primary == "PROXY_SIGNAL_GATE":
        return "fundamentals recovery improved the candidate, but proxy or consensus signal quality is still weak"
    if primary == "PORTFOLIO_RISK_GATE":
        return "candidate evidence improved, but portfolio risk controls still prevent promotion"
    if primary == "NON_CORE_WARNING_GATE":
        return "core blockers are resolved, but non-core warnings remain supporting-only"
    if core_blockers:
        return "core evidence blockers remain unresolved"
    if recovered:
        return "recovered fundamentals are visible, but no higher-level gate is strong enough to create pending review"
    return "no decisive promotion-ready signal was found"


def _next_fix(primary: str, secondary: list[str]) -> list[str]:
    mapping = {
        "THESIS_CONFIDENCE_GATE": "build claim graph / proxy / filing support for the inferred thesis",
        "FILING_FRESHNESS_GATE": "refresh latest annual or quarterly filing evidence",
        "EVIDENCE_QUALITY_GATE": "upgrade weak evidence to primary, fresh, field-linked evidence",
        "BEAR_CASE_GATE": "strengthen bear case response evidence and residual risk mitigation",
        "VALUATION_GATE": "refresh valuation price and strengthen peer or historical valuation support",
        "PROXY_SIGNAL_GATE": "repair proxy or consensus signal quality",
        "PORTFOLIO_RISK_GATE": "review portfolio exposure and position sizing constraints",
        "NON_CORE_WARNING_GATE": "resolve supporting and optional field warnings",
        "CORE_EVIDENCE_GATE": "recover missing core field evidence",
        "REVIEW_STATE_GATE": "keep reduced-size pending under human review; do not auto approve",
    }
    fixes = [mapping.get(primary, "inspect remaining promotion metadata")]
    fixes.extend(mapping[gate] for gate in secondary if gate in mapping and mapping[gate] not in fixes)
    return fixes[:4]


def classify_blocking_gates(
    *,
    row: dict[str, Any],
    phase6_row: dict[str, Any],
    freshness: dict[str, Any],
    evidence_quality: dict[str, Any],
) -> tuple[str, list[str], list[str]]:
    status = row.get("after_status") or row.get("status")
    core_blockers = _field_names(row.get("core_blockers") or [])
    primary_thesis = str(row.get("primary_thesis_type") or "unknown")
    confidence = float(row.get("thesis_inference_confidence") or ((row.get("thesis_inference") or {}).get("confidence") or 0.0))
    bear = _bear_case_gate(row, phase6_row)
    bear_status = str(bear.get("overall_status") or "").lower()
    bear_residual = str(bear.get("residual_risk_level") or bear.get("overall_residual_risk_level") or "").lower()
    filing_status = str(((freshness.get("filing_freshness") or {}).get("status") or "unknown")).lower()
    gates: list[str] = []
    warnings: list[str] = []

    if status == "pending_human_review":
        gates.append("REVIEW_STATE_GATE")
    if primary_thesis == "unknown" or confidence < 0.5:
        gates.append("THESIS_CONFIDENCE_GATE")
    if core_blockers:
        gates.append("CORE_EVIDENCE_GATE")
    if filing_status in {"stale", "missing", "unknown"}:
        gates.append("FILING_FRESHNESS_GATE")
    if bear_status in {"unresolved"} or bear_residual in {"high", "critical"}:
        gates.append("BEAR_CASE_GATE")
    elif bear_status == "partially_mitigated":
        gates.append("BEAR_CASE_GATE")
        warnings.append("bear_case_partially_mitigated")
    eq_status = str((evidence_quality.get("evidence_quality_gate") or {}).get("status") or "")
    if eq_status in {"blocked", "needs_attention"}:
        gates.append("EVIDENCE_QUALITY_GATE")
    elif eq_status == "pass_with_warnings":
        warnings.append("evidence_quality_warnings")
    if _valuation_gate_active(phase6_row):
        gates.append("VALUATION_GATE")
    if _proxy_gate_active(phase6_row):
        gates.append("PROXY_SIGNAL_GATE")
    if str(row.get("portfolio_risk_status") or "").lower() in {"blocked", "needs_attention"}:
        gates.append("PORTFOLIO_RISK_GATE")
    if _data_freshness_gate_active(phase6_row):
        gates.append("DATA_FRESHNESS_GATE")
    non_core = _field_names(row.get("supporting_warnings") or []) + _field_names(row.get("optional_warnings") or [])
    if non_core:
        gates.append("NON_CORE_WARNING_GATE")
        warnings.extend([f"non_core_warning:{field}" for field in non_core])

    gates = list(dict.fromkeys(gates))
    if not gates:
        gates = ["UNKNOWN_GATE"]
    precedence = [
        "REVIEW_STATE_GATE",
        "THESIS_CONFIDENCE_GATE",
        "CORE_EVIDENCE_GATE" if core_blockers else "",
        "FILING_FRESHNESS_GATE",
        "BEAR_CASE_GATE",
        "EVIDENCE_QUALITY_GATE",
        "VALUATION_GATE",
        "PROXY_SIGNAL_GATE",
        "PORTFOLIO_RISK_GATE",
        "DATA_FRESHNESS_GATE",
        "NON_CORE_WARNING_GATE",
        "UNKNOWN_GATE",
    ]
    primary = next((gate for gate in precedence if gate and gate in gates), "UNKNOWN_GATE")
    if not core_blockers and primary == "CORE_EVIDENCE_GATE":
        primary = next((gate for gate in gates if gate != "CORE_EVIDENCE_GATE"), "UNKNOWN_GATE")
    secondary = [gate for gate in gates if gate != primary]
    return primary, secondary, sorted(set(warnings))


def build_ticker_block_diagnostics(conn: sqlite3.Connection, ticker: str, *, watchlist_id: str = "ai_core") -> dict[str, Any]:
    ticker = normalize_ticker(ticker)
    phase14 = latest_phase14_validation(conn, watchlist_id)
    phase6 = latest_phase6_validation(conn)
    row = row_for_ticker(phase14, ticker)
    phase6_row = row_for_ticker(phase6, ticker, keys=("tickers", "ticker_results", "results"))
    if not row:
        row = {"ticker": ticker, "status": phase6_row.get("status") or "observation_only", "primary_thesis_type": "unknown"}
    freshness = build_filing_freshness(conn, ticker)
    evidence_quality = build_evidence_quality_gate(conn, ticker)
    primary, secondary, warnings = classify_blocking_gates(
        row=row,
        phase6_row=phase6_row,
        freshness=freshness,
        evidence_quality=evidence_quality,
    )
    core_blockers = _field_names(row.get("core_blockers") or [])
    recovered = recovered_fields_for_ticker(conn, ticker)
    status = row.get("after_status") or row.get("status") or phase6_row.get("status") or "observation_only"
    return {
        "ticker": ticker,
        "status": status,
        "primary_thesis_type": row.get("primary_thesis_type") or "unknown",
        "primary_blocking_gate": primary,
        "secondary_blocking_gates": secondary,
        "warnings": warnings,
        "core_blockers": core_blockers,
        "non_core_warnings": _field_names(row.get("supporting_warnings") or []) + _field_names(row.get("optional_warnings") or []),
        "recovered_fields": recovered,
        "phase6_missing_requirements": _phase6_missing_requirements(phase6_row),
        "filing_freshness": freshness.get("filing_freshness") or {},
        "evidence_quality_gate": evidence_quality.get("evidence_quality_gate") or {},
        "bear_case_gate": _bear_case_gate(row, phase6_row),
        "why_not_pending": _why_not_pending(primary, recovered, core_blockers),
        "next_fix": _next_fix(primary, secondary),
    }


def build_watchlist_block_diagnostics(
    conn: sqlite3.Connection,
    *,
    watchlist_id: str = "ai_core",
    tickers: list[str] | None = None,
) -> dict[str, Any]:
    tickers = tickers or parse_tickers(watchlist_id=watchlist_id)
    rows = [build_ticker_block_diagnostics(conn, ticker, watchlist_id=watchlist_id) for ticker in tickers]
    distribution = Counter(row.get("primary_blocking_gate") or "UNKNOWN_GATE" for row in rows)
    return {
        "generated_at": now_ts(),
        "watchlist_id": watchlist_id,
        "summary": {
            "tickers_checked": len(rows),
            "pending_human_review": sum(1 for row in rows if row.get("status") == "pending_human_review"),
            "candidate_shadow": sum(1 for row in rows if row.get("status") == "candidate_shadow"),
            "observation_only": sum(1 for row in rows if row.get("status") == "observation_only"),
            "core_blocker_count": sum(len(row.get("core_blockers") or []) for row in rows),
            "primary_blocking_gates": dict(distribution),
        },
        "ticker_results": rows,
    }
