#!/usr/bin/env python3
"""Phase 13 validation for thesis-aware core/non-core evidence gates."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
REPORTING_DIR = Path(__file__).resolve().parents[1] / "reporting"
for path in (LIB_DIR, REPORTING_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from build_phase12_data_quality_before_after import build_phase12_data_quality_report
from smr_agents import DB_PATH
from smr_bear_case_response import attach_bear_case_response, respond_to_bear_case
from smr_blocker_repair_queue import apply_phase13_core_gate_metadata
from smr_data_quality_gate import build_data_quality_gate
from smr_decision import ensure_decision_tables
from smr_fundamentals import build_fundamentals_snapshot, latest_fundamentals_snapshot
from smr_portfolio_risk import evaluate_portfolio_risk
from smr_recommendation_candidate import build_recommendation_candidate
from smr_recommendation_promotion import evaluate_promotion, promotion_to_dict
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_thesis_dependency import build_promotion_evidence_gate, infer_thesis_type_from_claims, load_thesis_requirements
from smr_valuation import build_valuation_snapshot, latest_valuation_snapshot
from smr_wiki import now_ts


SCRIPT_NAME = "validate_phase13_core_gate_repaired_candidate.py"


def loads_json(raw: str | None, fallback: Any) -> Any:
    if raw in (None, ""):
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def latest_registry_payload(conn: sqlite3.Connection, entity_type: str, entity_id: str | None = None) -> dict[str, Any]:
    params: list[Any] = [entity_type]
    where = "entity_type=?"
    if entity_id:
        where += " AND entity_id=?"
        params.append(entity_id.upper())
    row = conn.execute(
        f"""
        SELECT payload_json
        FROM task_registry_entry
        WHERE {where}
        ORDER BY datetime(created_at) DESC, snapshot_index DESC, id DESC
        LIMIT 1
        """,
        params,
    ).fetchone()
    return loads_json(row[0], {}) if row else {}


def _missing_fields_from_roots(root_causes: list[str]) -> list[str]:
    fields = []
    for item in root_causes or []:
        text = str(item or "")
        if ":" in text:
            fields.append(text.split(":", 1)[1])
    return sorted(set(fields))


def _field_names(rows: list[dict[str, Any]]) -> list[str]:
    return sorted({str(item.get("field")) for item in rows if isinstance(item, dict) and item.get("field")})


def _root_code_set(root_causes: list[str]) -> list[str]:
    return sorted({str(item).split(":", 1)[0] for item in root_causes if item})


def _source_evidence_count(fundamentals: dict[str, Any]) -> int:
    return sum(
        1
        for detail in (fundamentals.get("field_details") or {}).values()
        if isinstance(detail, dict) and detail.get("source_evidence_id")
    )


def _usable_field_count(fundamentals: dict[str, Any]) -> int:
    return sum(
        1
        for detail in (fundamentals.get("field_details") or {}).values()
        if isinstance(detail, dict)
        and detail.get("source_evidence_id")
        and detail.get("allowed_usage") in {"supporting_evidence", "promotion_evidence"}
    )


def _phase13_claims(thesis_types: list[str]) -> list[dict[str, Any]]:
    text = ", ".join(thesis_types)
    return [
        {
            "claim_id": "phase13_valuation_001",
            "claim_text": f"valuation rerating thesis requires peer and historical valuation support for {text}",
            "severity": "high",
        },
        {
            "claim_id": "phase13_data_quality_001",
            "claim_text": "fundamentals data quality remains weak if missing fields are core to thesis",
            "severity": "high",
        },
    ]


def _passing_data_health(ticker: str, valuation: dict[str, Any]) -> dict[str, Any]:
    market = valuation.get("market") or ("H" if ticker.upper().endswith(".HK") else "US")
    return {
        "overall_status": "fresh",
        "items": [
            {"data_type": "daily_bar", "market": market, "freshness_status": "fresh", "blocking_level": "none"},
            {"data_type": "news", "market": market, "freshness_status": "fresh", "blocking_level": "none"},
            {
                "data_type": "filings",
                "market": market,
                "freshness_status": "fresh",
                "blocking_level": "none",
                "metadata": {"ticker": ticker.upper()},
            },
        ],
    }


def _proxy_from_valuation(valuation: dict[str, Any], fundamentals: dict[str, Any]) -> dict[str, Any]:
    forward_eps = valuation.get("forward_eps") or {}
    evidence_ids = [
        detail.get("source_evidence_id")
        for detail in (fundamentals.get("field_details") or {}).values()
        if isinstance(detail, dict) and detail.get("source_evidence_id")
    ][:4]
    quality = forward_eps.get("proxy_quality") or forward_eps.get("quality") or "medium"
    usable = quality in {"medium", "strong"} or forward_eps.get("status") == "proxy"
    return {
        "ticker": valuation.get("ticker") or fundamentals.get("ticker"),
        "market": valuation.get("market") or fundamentals.get("market"),
        "status": forward_eps.get("status") or "proxy",
        "source": forward_eps.get("source") or "internal_proxy",
        "is_official_consensus": False,
        "official_consensus_active": False,
        "proxy_quality": quality,
        "usable_for_promotion": bool(usable),
        "evidence_ids": evidence_ids,
        "independent_source_count": max(2, len(set(evidence_ids))),
        "allowed_usage": "supporting_evidence",
    }


def _valuation_checks(valuation: dict[str, Any]) -> dict[str, Any]:
    peer = valuation.get("peer_comparison") or {}
    historical = valuation.get("historical_valuation") or {}
    metrics = historical.get("metrics") or {}
    return {
        "allowed_usage": valuation.get("allowed_usage"),
        "valuation_status": valuation.get("valuation_status"),
        "price_status": valuation.get("price_status"),
        "peer_comparison_status": peer.get("peer_comparison_status"),
        "peer_count_available": peer.get("peer_count_available") or valuation.get("peer_count_available"),
        "peer_count_required": peer.get("peer_count_required") or valuation.get("peer_count_required"),
        "historical_valuation_status": historical.get("status") or valuation.get("historical_percentile_status"),
        "historical_available_metrics": sorted(
            metric for metric, detail in metrics.items() if isinstance(detail, dict) and detail.get("status") == "available"
        ),
    }


def _portfolio_status(portfolio_risk: dict[str, Any], suggested: float) -> dict[str, Any]:
    status = str(portfolio_risk.get("status") or "pass").lower()
    adjusted = portfolio_risk.get("recommended_position_pct")
    if adjusted is None:
        adjusted = suggested
    return {
        "status": status,
        "risk_adjusted_position_pct": adjusted,
        "recommended_action": portfolio_risk.get("recommended_action"),
        "blocking_factors": portfolio_risk.get("blocking_factors") or [],
    }


def build_phase13_gates(
    ticker: str,
    thesis_types: list[str],
    data_quality_report: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    after_roots = (data_quality_report.get("after") or {}).get("root_causes") or []
    after_fields = data_quality_report.get("after_field_quality") or {}
    missing_fields = _missing_fields_from_roots(after_roots)
    field_gate = build_promotion_evidence_gate(
        ticker=ticker,
        thesis_types=thesis_types,
        missing_fields=missing_fields,
        field_details=after_fields,
    )
    data_quality_gate = build_data_quality_gate(
        ticker=ticker,
        thesis_types=field_gate.get("thesis_types") or thesis_types,
        root_causes=after_roots,
        field_quality=after_fields,
        before_status=(data_quality_report.get("after") or {}).get("data_quality_status"),
    )
    return field_gate, data_quality_gate


def validate_phase13_candidate(
    conn: sqlite3.Connection,
    ticker: str,
    *,
    days: int = 365,
    thesis: str | None = None,
    run_repairs: bool = False,
) -> dict[str, Any]:
    del days
    ticker = ticker.upper()
    ensure_decision_tables(conn)
    phase12_payload = latest_registry_payload(conn, "phase12_evidence_quality_repaired_candidate_validation", ticker)
    before_status = phase12_payload.get("after_status") or "candidate_shadow"
    before_promotion_allowed = bool(phase12_payload.get("promotion_allowed"))

    fundamentals = latest_fundamentals_snapshot(conn, ticker) or build_fundamentals_snapshot(conn, ticker, prefer_live=True)
    valuation = latest_valuation_snapshot(conn, ticker) or build_valuation_snapshot(conn, ticker)
    claims = _phase13_claims([thesis] if thesis else [])
    thesis_types = [thesis] if thesis else infer_thesis_type_from_claims(claims, {"ticker": ticker})
    config = load_thesis_requirements()
    if thesis_types[0] not in (config.get("thesis_requirements") or {}):
        thesis_types = config.get("default_thesis_types") or ["valuation_rerating"]

    data_quality_report = build_phase12_data_quality_report(
        conn,
        ticker,
        refresh_fundamentals=False,
        thesis_types=thesis_types,
    )
    field_gate, data_quality_gate = build_phase13_gates(ticker, thesis_types, data_quality_report)
    thesis_types = field_gate.get("thesis_types") or thesis_types
    bear_response = respond_to_bear_case(
        ticker,
        {"bear_case_claims": _phase13_claims(thesis_types), "deal_breakers": ["Core evidence blocker reappears"]},
        fundamentals_snapshot=fundamentals,
        valuation_snapshot=valuation,
        thesis_types=thesis_types,
        field_gate=field_gate,
        data_quality_gate=data_quality_gate,
    )
    bear_case = attach_bear_case_response(
        {
            "bear_case_strength": "high",
            "bear_case_claims": _phase13_claims(thesis_types),
            "deal_breakers": ["Core evidence blocker reappears"],
            "data_quality_risk": "high" if data_quality_gate.get("status") not in {"pass", "pass_with_warnings"} else "medium",
            "bear_case_gate": bear_response.get("bear_case_gate") or {},
            "data_quality_gate": data_quality_gate,
        },
        bear_response,
    )

    valuation_checks = _valuation_checks(valuation)
    evidence_count = _source_evidence_count(fundamentals)
    usable_field_count = _usable_field_count(fundamentals)
    dashboard = {
        "action": f"small_candidate {ticker}",
        "ticker": ticker,
        "theme": ",".join(thesis_types),
        "suggested_position_pct": 1.5,
        "max_position_pct": 3.0,
        "confidence_rationale": "Phase 13 thesis-aware reduced-size candidate validation.",
        "kill_triggers": ["Any thesis-core evidence field becomes missing or blocked."],
    }
    evidence_check = {
        "severity": "pass" if evidence_count >= 5 else "degrade",
        "evidence_summary": {
            "source_path_count": max(2, evidence_count),
            "primary_anchor_count": 1 if evidence_count else 0,
            "usable_for_promotion_count": usable_field_count,
        },
        "independent_source_count": max(2, evidence_count),
        "primary_evidence_count": 1 if evidence_count else 0,
    }
    claim_graph = {
        "unsupported_core_claims": [],
        "low_quality_core_claims": [],
        "counter_evidence_count": 1,
        "recommendation_allowed": True,
    }
    proxy = _proxy_from_valuation(valuation, fundamentals)
    reduced_policy = (config.get("reduced_size_policy") or {"default_multiplier": 0.5, "max_reduced_size_pct": 1.0})
    portfolio_risk = evaluate_portfolio_risk(
        conn,
        ticker=ticker,
        watchlist_item={"ticker": ticker, "market": valuation.get("market"), "theme": ",".join(thesis_types), "sector": "internet_platforms", "max_position_pct": 1.0},
        suggested_position_pct=1.0,
        max_position_pct=1.0,
        watchlist_name="ai_core",
        watchlist_items=[{"ticker": ticker, "market": valuation.get("market"), "theme": ",".join(thesis_types), "sector": "internet_platforms", "max_position_pct": 1.0}],
    )
    promotion = evaluate_promotion(
        conn,
        report_id=f"phase13_core_gate_report__{ticker}__{thesis_types[0]}",
        recommendation_id=f"phase13_core_gate__{ticker}__{thesis_types[0]}",
        from_status=before_status,
        dashboard_summary=dashboard,
        data_health_snapshot=_passing_data_health(ticker, valuation),
        evidence_check_snapshot=evidence_check,
        claim_graph_snapshot=claim_graph,
        valuation_snapshot=valuation,
        fundamentals_snapshot=fundamentals,
        consensus_proxy=proxy,
        bear_case=bear_case,
        risk_snapshot={"status": "pass"},
        lint_result={"max_severity": "info", "issues": []},
        thesis_types=thesis_types,
        promotion_evidence_gate=field_gate,
        data_quality_gate=data_quality_gate,
        bear_case_gate=bear_response.get("bear_case_gate") or {},
        reduced_size_policy=reduced_policy,
        write_ledger=True,
    )
    candidate = build_recommendation_candidate(
        conn,
        recommendation_id=f"phase13_core_gate__{ticker}__{thesis_types[0]}",
        ticker=ticker,
        report=dashboard,
        claim_graph=claim_graph,
        evidence_check=evidence_check,
        valuation_snapshot=valuation,
        consensus_proxy=proxy,
        bear_case=bear_case,
        risk_snapshot={"status": "pass"},
        portfolio_risk=portfolio_risk,
        market_signal={"signal": "positive"},
        promotion_result=promotion,
        write_ledger=True,
    )
    repair_queue_update = apply_phase13_core_gate_metadata(
        conn,
        ticker=ticker,
        field_gate=field_gate,
        data_quality_gate=data_quality_gate,
        watchlist_id="ai_core",
    )
    remaining = []
    if field_gate.get("core_blockers"):
        remaining.append("CORE_EVIDENCE_BLOCKER")
    if data_quality_gate.get("status") in {"degraded_core", "blocked"}:
        remaining.append("DATA_QUALITY_RISK")
    if (bear_response.get("bear_case_gate") or {}).get("has_critical_unresolved_core_risk"):
        remaining.append("HIGH_BEAR_CASE_UNRESOLVED")
    elif candidate.get("status") != "pending_human_review" and bear_response.get("overall_response_status") == "partially_mitigated":
        remaining.append("HIGH_BEAR_CASE_PARTIALLY_MITIGATED")
    if portfolio_risk.get("status") == "block":
        remaining.append("RISK_LIMIT_EXCEEDED")
    remaining = sorted(set(remaining))
    reclassified_warnings = []
    if data_quality_gate.get("status") == "degraded_non_core":
        reclassified_warnings.append("DATA_QUALITY_RISK")
    if field_gate.get("optional_warnings") or field_gate.get("supporting_warnings"):
        reclassified_warnings.append("FIELD_NOT_FOUND")
    if (
        bear_response.get("overall_response_status") == "partially_mitigated"
        and not (bear_response.get("bear_case_gate") or {}).get("has_critical_unresolved_core_risk")
        and not field_gate.get("core_blockers")
        and data_quality_gate.get("status") not in {"degraded_core", "blocked"}
    ):
        reclassified_warnings.append("HIGH_BEAR_CASE_PARTIALLY_MITIGATED")

    payload = {
        "generated_at": now_ts(),
        "ticker": ticker,
        "thesis_type": thesis_types[0] if len(thesis_types) == 1 else thesis_types,
        "thesis_types": thesis_types,
        "before_status": before_status,
        "before_promotion_allowed": before_promotion_allowed,
        "after_status": candidate.get("status"),
        "promotion_allowed": bool(promotion.allowed),
        "promotion_mode": candidate.get("promotion_mode"),
        "action": candidate.get("action"),
        "position_policy": candidate.get("position_policy"),
        "suggested_position_pct": candidate.get("suggested_position_pct"),
        "max_position_pct": candidate.get("max_position_pct"),
        "field_gate": {
            "core_blockers": _field_names(field_gate.get("core_blockers") or []),
            "supporting_warnings": _field_names(field_gate.get("supporting_warnings") or []),
            "optional_warnings": _field_names(field_gate.get("optional_warnings") or []),
            "unknown_warnings": _field_names(field_gate.get("unknown_warnings") or []),
            "gate_status": field_gate.get("gate_status"),
            "detail": field_gate,
        },
        "data_quality_gate": {
            "status": data_quality_gate.get("status"),
            "before_status": data_quality_gate.get("before_status"),
            "after_status": data_quality_gate.get("after_status"),
            "core_issues": data_quality_gate.get("core_issues") or [],
            "non_core_issues": data_quality_gate.get("non_core_issues") or [],
            "unknown_issues": data_quality_gate.get("unknown_issues") or [],
            "action_effect": data_quality_gate.get("action_effect"),
        },
        "bear_case_gate": bear_response.get("bear_case_gate") or {},
        "bear_case_response": {
            "overall_status": bear_response.get("overall_response_status"),
            "action_effect": bear_response.get("action_effect"),
            "responses": bear_response.get("responses") or [],
        },
        "valuation": valuation_checks,
        "portfolio_risk": _portfolio_status(portfolio_risk, float(candidate.get("suggested_position_pct") or 0.0)),
        "proxy": {
            "proxy_quality": proxy.get("proxy_quality"),
            "is_official_consensus": bool(proxy.get("is_official_consensus")),
            "source": proxy.get("source"),
        },
        "candidate": {
            "recommendation_id": candidate.get("recommendation_id"),
            "ticker": candidate.get("ticker"),
            "action": candidate.get("action"),
            "status": candidate.get("status"),
            "confidence": candidate.get("confidence"),
            "suggested_position_pct": candidate.get("suggested_position_pct"),
            "max_position_pct": candidate.get("max_position_pct"),
            "promotion_mode": candidate.get("promotion_mode"),
            "position_policy": candidate.get("position_policy"),
            "reasons": candidate.get("reasons") or [],
        },
        "promotion": {
            "allowed": bool(promotion.allowed),
            "to_status": promotion.to_status,
            "missing_requirements": promotion.missing_requirements,
            "required_fixes": promotion.required_fixes,
            "reasons": promotion.reasons,
        },
        "data_quality": {
            "before": (data_quality_report.get("before") or {}).get("data_quality_status"),
            "after": (data_quality_report.get("after") or {}).get("data_quality_status"),
            "remaining_root_causes": data_quality_report.get("remaining_root_causes") or [],
            "root_cause_codes": _root_code_set(data_quality_report.get("remaining_root_causes") or []),
        },
        "blockers_resolved": [],
        "blockers_reclassified_as_warnings": sorted(set(reclassified_warnings)),
        "blockers_remaining": remaining,
        "decision_ledger_written": bool(
            conn.execute(
                "SELECT 1 FROM decision_ledger WHERE recommendation_id=?",
                (f"phase13_core_gate__{ticker}__{thesis_types[0]}",),
            ).fetchone()
        ),
        "repair_queue_updates": repair_queue_update,
        "run_repairs": run_repairs,
    }
    register_snapshot(
        conn,
        entity_type="phase13_core_gate_repaired_candidate_validation",
        entity_id=ticker,
        status=str(payload.get("after_status") or "unknown"),
        source=SCRIPT_NAME,
        payload=payload,
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 13 thesis-aware core/non-core candidate gate")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker", default="09988.HK")
    parser.add_argument("--days", type=int, default=365)
    parser.add_argument("--thesis", default=None)
    parser.add_argument("--run-repairs", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db_path)
    conn.row_factory = sqlite3.Row
    try:
        payload = validate_phase13_candidate(
            conn,
            args.ticker,
            days=args.days,
            thesis=args.thesis,
            run_repairs=args.run_repairs,
        )
        conn.commit()
    finally:
        conn.close()
    print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase13 core gate repaired candidate validation complete", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
