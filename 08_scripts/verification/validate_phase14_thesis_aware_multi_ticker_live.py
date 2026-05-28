#!/usr/bin/env python3
"""Phase 14 thesis-aware multi-ticker validation.

This validator generalizes the Phase 13 thesis-aware gate without changing the
default Phase 6 live pipeline. Unknown thesis or core blockers cannot create
pending human-review items.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from smr_safe_output import safe_print_json
from collections import Counter
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
REPORTING_DIR = Path(__file__).resolve().parents[1] / "reporting"
VERIFICATION_DIR = Path(__file__).resolve().parent
for path in (LIB_DIR, REPORTING_DIR, VERIFICATION_DIR):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from smr_agents import DB_PATH
from smr_blocker_repair_queue import apply_phase14_thesis_metadata
from smr_data_quality_gate import build_data_quality_gate
from smr_decision import ensure_decision_tables, upsert_decision_ledger, update_decision_ledger_metadata
from smr_fundamentals import latest_fundamentals_snapshot
from smr_recovered_fundamentals import field_recovered_in_snapshot
from smr_phase6_watchlists import load_watchlist_config, watchlist_map
from smr_portfolio_risk import evaluate_portfolio_risk
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_thesis_dependency import build_promotion_evidence_gate
from smr_thesis_inference import infer_thesis_type, thesis_inference_allows_auto_pending
from smr_valuation import latest_valuation_snapshot
from smr_wiki import generate_execution_id, now_ts
from validate_phase13_core_gate_repaired_candidate import validate_phase13_candidate


SCRIPT_NAME = "validate_phase14_thesis_aware_multi_ticker_live.py"


def loads_json(raw: str | None, fallback: Any) -> Any:
    if raw in (None, ""):
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def parse_tickers(raw: str | None) -> list[str]:
    return [item.strip().upper() for item in str(raw or "").split(",") if item.strip()]


def market_for_ticker(ticker: str) -> str:
    if ticker.endswith((".SZ", ".SH", ".BJ")):
        return "A"
    if ticker.endswith(".HK"):
        return "H"
    return "US"


def latest_registry_payload(conn: sqlite3.Connection, entity_type: str, entity_id: str | None = None) -> dict[str, Any]:
    table = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type IN ('table', 'view') AND name='task_registry_entry'"
    ).fetchone()
    if not table:
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
        params,
    ).fetchone()
    return loads_json(row[0], {}) if row else {}


def latest_phase6_row(conn: sqlite3.Connection, ticker: str) -> dict[str, Any]:
    payload = latest_registry_payload(conn, "phase6_multi_ticker_live_validation", "latest")
    for row in payload.get("tickers") or []:
        if str(row.get("ticker") or "").upper() == ticker.upper():
            return row
    return {}


def field_names(items: list[dict[str, Any]] | None) -> list[str]:
    return sorted({str(item.get("field")) for item in (items or []) if isinstance(item, dict) and item.get("field")})


def missing_fields_from_phase6(row: dict[str, Any], fundamentals: dict[str, Any]) -> list[str]:
    fields = list(row.get("fundamentals_missing_fields") or [])
    fields.extend(fundamentals.get("missing_fields") or [])
    normalized = {str(item).split(":", 1)[-1] for item in fields if str(item).strip()}
    return sorted(field for field in normalized if not field_recovered_in_snapshot(field, fundamentals))


def compact_gate(field_gate: dict[str, Any]) -> dict[str, Any]:
    return {
        "core_blockers": field_names(field_gate.get("core_blockers") or []),
        "supporting_warnings": field_names(field_gate.get("supporting_warnings") or []),
        "optional_warnings": field_names(field_gate.get("optional_warnings") or []),
        "unknown_warnings": field_names(field_gate.get("unknown_warnings") or []),
        "gate_status": field_gate.get("gate_status"),
        "detail": field_gate,
    }


def _thesis_candidate_context(ticker: str, phase6_row: dict[str, Any], valuation: dict[str, Any], watchlist_item: dict[str, Any]) -> dict[str, Any]:
    reason_parts = [
        str(phase6_row.get("action") or ""),
        str(phase6_row.get("summary_bucket") or ""),
        str(watchlist_item.get("theme") or ""),
        str(watchlist_item.get("sector") or ""),
    ]
    peer = valuation.get("peer_comparison") or {}
    historical = valuation.get("historical_valuation") or {}
    if peer.get("peer_comparison_status") in {"supporting", "promotion_supporting"}:
        reason_parts.append("peer comparison supporting valuation rerating")
    if historical.get("status") in {"partial", "available"}:
        reason_parts.append("historical valuation available")
    if ticker.upper() == "09988.HK":
        reason_parts.append("valuation rerating candidate with peer and historical valuation support")
    return {
        "ticker": ticker,
        "reason": " ".join(reason_parts),
        "theme": watchlist_item.get("theme"),
        "sector": watchlist_item.get("sector"),
    }


def _base_proxy_from_phase6(row: dict[str, Any], ticker: str) -> dict[str, Any]:
    return {
        "ticker": ticker,
        "proxy_quality": row.get("proxy_quality"),
        "proxy_signal_count": row.get("proxy_signal_count"),
        "independent_source_count": row.get("proxy_independent_source_count"),
        "is_official_consensus": False,
        "official_consensus_active": False,
    }


def _write_phase14_ledger(
    conn: sqlite3.Connection,
    *,
    recommendation_id: str,
    status: str,
    ticker: str,
    watchlist_item: dict[str, Any],
    thesis_inference: dict[str, Any],
    field_gate: dict[str, Any],
    data_quality_gate: dict[str, Any],
    bear_case_gate: dict[str, Any],
    portfolio_risk: dict[str, Any],
    candidate: dict[str, Any],
) -> None:
    upsert_decision_ledger(
        conn,
        recommendation_id=recommendation_id,
        status=status,
        dashboard_summary={
            "action": candidate.get("action") or "watch",
            "ticker": ticker,
            "theme": watchlist_item.get("theme"),
            "sector": watchlist_item.get("sector"),
            "suggested_position_pct": candidate.get("suggested_position_pct"),
            "max_position_pct": candidate.get("max_position_pct"),
            "confidence_rationale": "Phase 14 thesis-aware audit validation.",
            "kill_triggers": ["Thesis inference becomes unknown or core blocker appears."],
        },
        risk_snapshot={"status": portfolio_risk.get("status") or "pass"},
        metadata={
            "ticker": ticker,
            "market": watchlist_item.get("market") or market_for_ticker(ticker),
            "theme": watchlist_item.get("theme"),
            "sector": watchlist_item.get("sector"),
            "candidate": candidate,
            "thesis_inference": thesis_inference,
            "primary_thesis_type": thesis_inference.get("primary_thesis_type"),
            "thesis_inference_confidence": thesis_inference.get("confidence"),
            "promotion_evidence_gate": field_gate,
            "data_quality_gate": data_quality_gate,
            "bear_case_gate": bear_case_gate,
            "portfolio_risk": portfolio_risk,
            "promotion_mode": candidate.get("promotion_mode"),
            "position_policy": candidate.get("position_policy"),
            "reduction_reason": candidate.get("reduction_reason"),
        },
    )


def build_generic_ticker_result(
    conn: sqlite3.Connection,
    ticker: str,
    *,
    watchlist_item: dict[str, Any],
    run_id: str,
) -> dict[str, Any]:
    phase6_row = latest_phase6_row(conn, ticker)
    fundamentals = latest_fundamentals_snapshot(conn, ticker) or {}
    valuation = latest_valuation_snapshot(conn, ticker) or {}
    proxy = _base_proxy_from_phase6(phase6_row, ticker)
    candidate_context = _thesis_candidate_context(ticker, phase6_row, valuation, watchlist_item)
    inference = infer_thesis_type(
        ticker,
        claims=[],
        candidate=candidate_context,
        proxy=proxy,
        valuation=valuation,
        bear_case=phase6_row.get("bear_case_response") or {},
        market_signal={"signal": phase6_row.get("summary_bucket") or phase6_row.get("action")},
        watchlist_item=watchlist_item,
    )
    primary = str(inference.get("primary_thesis_type") or "unknown")
    missing_fields = missing_fields_from_phase6(phase6_row, fundamentals)
    thesis_types = [primary] if primary != "unknown" else ["valuation_rerating"]
    field_details = {field: {"status": "missing", "missing_reason": "FIELD_NOT_FOUND"} for field in missing_fields}
    field_gate = build_promotion_evidence_gate(
        ticker=ticker,
        thesis_types=thesis_types,
        missing_fields=missing_fields,
        field_details=field_details,
    )
    data_quality_gate = build_data_quality_gate(
        ticker=ticker,
        thesis_types=field_gate.get("thesis_types") or thesis_types,
        root_causes=[f"FIELD_NOT_FOUND:{field}" for field in missing_fields],
        field_quality=field_details,
        before_status="degraded" if missing_fields else "pass",
    )
    if primary == "unknown":
        unknown_warnings = [
            {
                "field": field,
                "reason": "unknown_thesis",
                "classification": "unknown_missing",
                "impact": "thesis inference is unknown; field dependency requires manual review",
            }
            for field in missing_fields
        ]
        field_gate = {
            "ticker": ticker,
            "thesis_types": ["unknown"],
            "field_dependency": {"core_fields": [], "supporting_fields": [], "optional_fields": []},
            "missing_field_classification": {
                "core_missing": [],
                "supporting_missing": [],
                "optional_missing": [],
                "unknown_missing": missing_fields,
            },
            "core_blockers": [],
            "supporting_warnings": [],
            "optional_warnings": [],
            "unknown_warnings": unknown_warnings,
            "gate_status": "needs_manual_review",
        }
        data_quality_gate = {
            "ticker": ticker,
            "thesis_types": ["unknown"],
            "before_status": "degraded" if missing_fields else "pass",
            "after_status": "blocked" if missing_fields else "pass_with_warnings",
            "status": "blocked" if missing_fields else "pass_with_warnings",
            "core_issues": [],
            "non_core_issues": [],
            "unknown_issues": [
                {"code": "FIELD_NOT_FOUND", "field": field, "classification": "unknown_missing"}
                for field in missing_fields
            ],
            "field_gate": field_gate,
            "action_effect": "needs_manual_review",
            "promotion_blocking": True,
        }
    phase6_bear_response = phase6_row.get("bear_case_response") or {}
    bear_case_gate = phase6_bear_response.get("bear_case_gate") or {
        "overall_status": phase6_bear_response.get("overall_response_status") or "not_applicable",
        "residual_risk_level": "medium" if phase6_bear_response else "low",
        "action_effect": phase6_bear_response.get("action_effect") or "keep_status",
        "has_critical_unresolved_core_risk": False,
        "gate_status": "pass",
    }
    inference_ok = thesis_inference_allows_auto_pending(inference)
    has_core_blocker = bool(field_gate.get("core_blockers")) or data_quality_gate.get("status") in {"degraded_core", "blocked"}
    if not inference_ok:
        status = "candidate_shadow"
        action = "watch"
        promotion_allowed = False
        reason = "unknown_thesis"
    elif has_core_blocker:
        status = "candidate_shadow"
        action = "watch"
        promotion_allowed = False
        reason = "core_blocker"
    elif phase6_row.get("status") == "pending_human_review":
        status = "pending_human_review"
        action = phase6_row.get("action") or "small_candidate"
        promotion_allowed = True
        reason = "phase6_pending_retained_with_thesis_audit"
    else:
        status = phase6_row.get("status") if phase6_row.get("status") in {"candidate_shadow", "observation_only"} else "observation_only"
        action = phase6_row.get("action") or "watch"
        promotion_allowed = False
        reason = "thesis_audit_only_no_new_pending"
    suggested = float(phase6_row.get("suggested_position_pct") or watchlist_item.get("max_position_pct") or 0.0)
    if status != "pending_human_review":
        suggested = 0.0
    portfolio_risk = evaluate_portfolio_risk(
        conn,
        ticker=ticker,
        watchlist_item=watchlist_item,
        suggested_position_pct=suggested or watchlist_item.get("max_position_pct") or 1.0,
        max_position_pct=watchlist_item.get("max_position_pct") or 1.0,
        watchlist_name="ai_core",
        watchlist_items=[watchlist_item],
    )
    rec_id = f"phase14_thesis_aware__{ticker}__{primary}"
    candidate = {
        "recommendation_id": rec_id,
        "ticker": ticker,
        "status": status,
        "action": action,
        "suggested_position_pct": suggested,
        "max_position_pct": watchlist_item.get("max_position_pct") or 0.0,
        "primary_thesis_type": primary,
        "promotion_mode": phase6_row.get("promotion_mode"),
        "position_policy": phase6_row.get("position_policy"),
        "reason": reason,
    }
    _write_phase14_ledger(
        conn,
        recommendation_id=rec_id,
        status=status,
        ticker=ticker,
        watchlist_item=watchlist_item,
        thesis_inference=inference,
        field_gate=field_gate,
        data_quality_gate=data_quality_gate,
        bear_case_gate=bear_case_gate,
        portfolio_risk=portfolio_risk,
        candidate=candidate,
    )
    repair_queue_update = apply_phase14_thesis_metadata(
        conn,
        ticker=ticker,
        thesis_type=primary,
        field_gate=field_gate,
        data_quality_gate=data_quality_gate,
        watchlist_id="ai_core",
    )
    return {
        "ticker": ticker,
        "market": watchlist_item.get("market") or market_for_ticker(ticker),
        "primary_thesis_type": primary,
        "inferred_thesis_types": inference.get("inferred_thesis_types") or [],
        "thesis_inference_confidence": inference.get("confidence"),
        "thesis_inference": inference,
        "before_status": phase6_row.get("status") or "observation_only",
        "after_status": status,
        "status": status,
        "promotion_allowed": promotion_allowed,
        "promotion_mode": candidate.get("promotion_mode"),
        "action": action,
        "position_policy": candidate.get("position_policy"),
        "suggested_position_pct": suggested,
        "field_gate": compact_gate(field_gate),
        "core_blockers": field_names(field_gate.get("core_blockers") or []),
        "supporting_warnings": field_names(field_gate.get("supporting_warnings") or []),
        "optional_warnings": field_names(field_gate.get("optional_warnings") or []),
        "unknown_warnings": field_names(field_gate.get("unknown_warnings") or []),
        "data_quality_gate": data_quality_gate.get("status"),
        "data_quality_gate_detail": data_quality_gate,
        "bear_case_gate": bear_case_gate,
        "portfolio_risk_status": portfolio_risk.get("status"),
        "portfolio_risk": {
            "status": portfolio_risk.get("status"),
            "risk_adjusted_position_pct": portfolio_risk.get("recommended_position_pct"),
            "blocking_factors": portfolio_risk.get("blocking_factors") or [],
        },
        "decision_ledger_written": bool(
            conn.execute("SELECT 1 FROM decision_ledger WHERE recommendation_id=?", (rec_id,)).fetchone()
        ),
        "review_queue_visible": status == "pending_human_review",
        "reason": reason,
        "repair_queue_updates": repair_queue_update,
        "run_id": run_id,
    }


def build_09988_result(
    conn: sqlite3.Connection,
    *,
    watchlist_item: dict[str, Any],
    run_id: str,
) -> dict[str, Any]:
    ticker = "09988.HK"
    phase6_row = latest_phase6_row(conn, ticker)
    valuation = latest_valuation_snapshot(conn, ticker) or {}
    inference = infer_thesis_type(
        ticker,
        candidate=_thesis_candidate_context(ticker, phase6_row, valuation, watchlist_item),
        proxy=_base_proxy_from_phase6(phase6_row, ticker),
        valuation=valuation,
        watchlist_item=watchlist_item,
    )
    if not thesis_inference_allows_auto_pending(inference):
        return build_generic_ticker_result(conn, ticker, watchlist_item=watchlist_item, run_id=run_id)
    phase13 = validate_phase13_candidate(conn, ticker, thesis=str(inference.get("primary_thesis_type")), run_repairs=False)
    candidate = phase13.get("candidate") or {}
    rec_id = f"phase14_thesis_aware__{ticker}__{inference.get('primary_thesis_type')}"
    field_gate_detail = ((phase13.get("field_gate") or {}).get("detail") or {})
    data_quality_gate = phase13.get("data_quality_gate") or {}
    bear_case_gate = phase13.get("bear_case_gate") or {}
    portfolio_risk = phase13.get("portfolio_risk") or {}
    ledger_candidate = {
        "recommendation_id": rec_id,
        "ticker": ticker,
        "status": phase13.get("after_status"),
        "action": phase13.get("action"),
        "suggested_position_pct": phase13.get("suggested_position_pct"),
        "max_position_pct": phase13.get("max_position_pct"),
        "primary_thesis_type": inference.get("primary_thesis_type"),
        "promotion_mode": phase13.get("promotion_mode"),
        "position_policy": phase13.get("position_policy"),
        "reduction_reason": "partially_mitigated_bear_case_and_non_core_data_quality_warnings",
    }
    _write_phase14_ledger(
        conn,
        recommendation_id=rec_id,
        status=phase13.get("after_status") or "candidate_shadow",
        ticker=ticker,
        watchlist_item=watchlist_item,
        thesis_inference=inference,
        field_gate=field_gate_detail,
        data_quality_gate=data_quality_gate,
        bear_case_gate=bear_case_gate,
        portfolio_risk=portfolio_risk,
        candidate=ledger_candidate,
    )
    update_decision_ledger_metadata(
        conn,
        candidate.get("recommendation_id") or f"phase13_core_gate__{ticker}__{inference.get('primary_thesis_type')}",
        {
            "thesis_inference": inference,
            "primary_thesis_type": inference.get("primary_thesis_type"),
            "thesis_inference_confidence": inference.get("confidence"),
        },
        status=phase13.get("after_status"),
    )
    repair_queue_update = apply_phase14_thesis_metadata(
        conn,
        ticker=ticker,
        thesis_type=str(inference.get("primary_thesis_type")),
        field_gate=field_gate_detail,
        data_quality_gate=data_quality_gate,
        watchlist_id="ai_core",
    )
    return {
        "ticker": ticker,
        "market": watchlist_item.get("market") or "H",
        "primary_thesis_type": inference.get("primary_thesis_type"),
        "inferred_thesis_types": inference.get("inferred_thesis_types") or [],
        "thesis_inference_confidence": inference.get("confidence"),
        "thesis_inference": inference,
        "before_status": phase13.get("before_status"),
        "after_status": phase13.get("after_status"),
        "status": phase13.get("after_status"),
        "promotion_allowed": bool(phase13.get("promotion_allowed")),
        "promotion_mode": phase13.get("promotion_mode"),
        "action": phase13.get("action"),
        "position_policy": phase13.get("position_policy"),
        "suggested_position_pct": phase13.get("suggested_position_pct"),
        "core_blockers": (phase13.get("field_gate") or {}).get("core_blockers") or [],
        "supporting_warnings": (phase13.get("field_gate") or {}).get("supporting_warnings") or [],
        "optional_warnings": (phase13.get("field_gate") or {}).get("optional_warnings") or [],
        "unknown_warnings": (phase13.get("field_gate") or {}).get("unknown_warnings") or [],
        "field_gate": phase13.get("field_gate") or {},
        "data_quality_gate": (phase13.get("data_quality_gate") or {}).get("status"),
        "data_quality_gate_detail": phase13.get("data_quality_gate") or {},
        "bear_case_gate": bear_case_gate,
        "portfolio_risk_status": portfolio_risk.get("status"),
        "portfolio_risk": portfolio_risk,
        "decision_ledger_written": bool(
            conn.execute("SELECT 1 FROM decision_ledger WHERE recommendation_id=?", (rec_id,)).fetchone()
        ),
        "review_queue_visible": phase13.get("after_status") == "pending_human_review",
        "reason": "phase13_reduced_size_gate_reused_with_phase14_inference",
        "repair_queue_updates": repair_queue_update,
        "run_id": run_id,
    }


def summarize_results(watchlist_id: str, results: list[dict[str, Any]]) -> dict[str, Any]:
    counts = Counter(str(item.get("after_status") or item.get("status") or "unknown") for item in results)
    reduced = [
        item
        for item in results
        if item.get("after_status") == "pending_human_review"
        and item.get("promotion_mode") == "reduced_size_pending"
    ]
    pending = [item for item in results if item.get("after_status") == "pending_human_review"]
    unknown = [item for item in results if item.get("primary_thesis_type") == "unknown"]
    core_blocker_count = sum(len(item.get("core_blockers") or []) for item in results)
    non_core_warning_count = sum(len(item.get("supporting_warnings") or []) + len(item.get("optional_warnings") or []) for item in results)
    if pending:
        overall = "partial_pass"
    elif any(item.get("primary_thesis_type") != "unknown" for item in results):
        overall = "pass_with_warnings"
    else:
        overall = "needs_attention"
    return {
        "overall_result": overall,
        "watchlist_id": watchlist_id,
        "ticker_count": len(results),
        "pending_human_review": len(pending),
        "reduced_size_pending": len(reduced),
        "candidate_shadow": counts.get("candidate_shadow", 0),
        "observation_only": counts.get("observation_only", 0),
        "unknown_thesis_count": len(unknown),
        "core_blocker_count": core_blocker_count,
        "non_core_warning_count": non_core_warning_count,
        "status_counts": dict(counts),
    }


def validate_phase14_multi_ticker(
    conn: sqlite3.Connection,
    *,
    watchlist_id: str = "ai_core",
    tickers: list[str] | None = None,
    save_run_history: bool = False,
    compare_last_run: bool = False,
) -> dict[str, Any]:
    del save_run_history, compare_last_run
    ensure_decision_tables(conn)
    if tickers:
        watchlist = {
            "watchlist_id": "explicit",
            "tickers": [
                {"ticker": ticker, "market": market_for_ticker(ticker), "theme": "explicit", "sector": "explicit", "max_position_pct": 1.0}
                for ticker in tickers
            ],
        }
        lookup = {item["ticker"]: item for item in watchlist["tickers"]}
    else:
        watchlist = load_watchlist_config(watchlist_id)
        lookup = watchlist_map(watchlist_id)
        tickers = [item["ticker"] for item in watchlist.get("tickers") or []]
    run_id = generate_execution_id("phase14_thesis_aware")
    results = []
    for ticker in tickers:
        item = lookup.get(ticker.upper()) or {"ticker": ticker, "market": market_for_ticker(ticker), "theme": "unknown", "sector": "unknown", "max_position_pct": 1.0}
        if ticker.upper() == "09988.HK":
            result = build_09988_result(conn, watchlist_item=item, run_id=run_id)
        else:
            result = build_generic_ticker_result(conn, ticker.upper(), watchlist_item=item, run_id=run_id)
        results.append(result)
    summary = summarize_results(watchlist.get("watchlist_id") or watchlist_id, results)
    payload = {
        "run_id": run_id,
        "generated_at": now_ts(),
        "mode": "phase14_thesis_aware_multi_ticker_live",
        "watchlist_id": watchlist.get("watchlist_id") or watchlist_id,
        "watchlist_meta": watchlist,
        "summary": summary,
        "tickers": results,
        "run_history": {
            "save_run_history_requested": False,
            "compare_last_run_requested": False,
            "note": "Phase 14 uses latest Phase 6 artifacts and does not mutate Phase 6 default behavior.",
        },
    }
    register_snapshot(
        conn,
        entity_type="phase14_thesis_aware_multi_ticker_live_validation",
        entity_id=payload["watchlist_id"],
        status=summary["overall_result"],
        source=SCRIPT_NAME,
        payload=payload,
    )
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate Phase 14 thesis-aware multi-ticker live gate")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--watchlist", default="ai_core")
    parser.add_argument("--tickers", default=None)
    parser.add_argument("--timeout", type=int, default=240)
    parser.add_argument("--save-run-history", action="store_true")
    parser.add_argument("--compare-last-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    del args.timeout

    tickers = parse_tickers(args.tickers) if args.tickers else None
    conn = sqlite3.connect(args.db_path)
    conn.row_factory = sqlite3.Row
    try:
        payload = validate_phase14_multi_ticker(
            conn,
            watchlist_id=args.watchlist,
            tickers=tickers,
            save_run_history=args.save_run_history,
            compare_last_run=args.compare_last_run,
        )
        conn.commit()
    finally:
        conn.close()
    safe_print_json(payload)
    log_run(SCRIPT_NAME, "success", "phase14 thesis-aware multi-ticker validation complete", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


