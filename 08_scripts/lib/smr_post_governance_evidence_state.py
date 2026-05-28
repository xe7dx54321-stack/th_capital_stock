#!/usr/bin/env python3
"""Phase 34 post-governance research revalidation helpers.

This module is intentionally read-only. It folds Phase 33 audit/lifecycle
outcomes back into ticker-level research diagnostics without creating pending
reviews, promotion evidence, paper orders, or trades.
"""

from __future__ import annotations

import sqlite3
from collections import Counter, defaultdict
from typing import Any

from smr_controlled_review_plan import phase33_audits
from smr_download_repair_queue import list_download_repair_tasks
from smr_evidence_lifecycle import list_lifecycle_states, list_semantic_evidence_candidates
from smr_evidence_review_workbench import COMPANY_NAMES
from smr_expectation_gap import build_expectation_gap
from smr_phase25_utils import resolve_phase25_tickers
from smr_supply_chain_variable_evidence import SEMANTIC_VARIABLE_MAP, build_variable_evidence_packs
from smr_wiki import now_ts


VARIABLE_SCOPE = [
    "supplier_share",
    "ASP_price_proxy",
    "capacity",
    "shipment",
    "customer_allocation_proxy",
    "consensus_expectation_proxy",
    "industry_forecast",
    "product_exposure",
    "margin_signal",
    "order_visibility",
]

CORE_GAP_VARIABLES = [
    "supplier_share",
    "ASP_price_proxy",
    "customer_allocation_proxy",
    "official_consensus",
]

ACTION_STRENGTHENING = {"approve_evidence", "link_to_variable_pack"}
ACTION_WEAKENING = {"downgrade_usage", "reject_evidence", "mark_as_noise", "request_better_source"}
INACTIVE_LIFECYCLE_STATUSES = {"rejected_evidence", "marked_noise", "removed", "archived"}


def resolve_phase34_tickers(ticker: str | None = None, tickers: str | None = None) -> list[str]:
    return resolve_phase25_tickers(ticker or tickers)


def normalize_research_variable(variable_type: str | None) -> str:
    raw = str(variable_type or "unknown")
    if raw in VARIABLE_SCOPE or raw in CORE_GAP_VARIABLES:
        return raw
    if raw == "official_consensus":
        return "official_consensus"
    if raw in {"consensus", "consensus_signal", "expectation_signal", "internal_consensus_proxy"}:
        return "consensus_expectation_proxy"
    if raw == "shipment_signal":
        return "shipment"
    if raw == "order_visibility_signal":
        return "order_visibility"
    return SEMANTIC_VARIABLE_MAP.get(raw, raw)


def _candidate_by_id(conn: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    return {str(row.get("evidence_id")): row for row in list_semantic_evidence_candidates(conn)}


def _state_by_id(conn: sqlite3.Connection) -> dict[str, dict[str, Any]]:
    return {str(row.get("evidence_id")): row for row in list_lifecycle_states(conn)}


def _reviewed_ids(audits: list[dict[str, Any]]) -> set[str]:
    return {str(row.get("evidence_id")) for row in audits if row.get("evidence_id")}


def _action_counts(audits: list[dict[str, Any]]) -> Counter[str]:
    return Counter(str(row.get("action") or "unknown") for row in audits)


def _after_counts(audits: list[dict[str, Any]]) -> Counter[str]:
    return Counter(str(row.get("after_status") or "unknown") for row in audits)


def _variable_changes(
    audits: list[dict[str, Any]],
    candidates: dict[str, dict[str, Any]],
    states: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    strengthened: list[str] = []
    weakened: list[str] = []
    needs_better: list[str] = []
    inactive_evidence_ids: list[str] = []
    rows: list[dict[str, Any]] = []
    for audit in audits:
        evidence_id = str(audit.get("evidence_id") or "")
        candidate = candidates.get(evidence_id) or {}
        state = states.get(evidence_id) or {}
        variable = normalize_research_variable(candidate.get("variable_type") or state.get("variable_type"))
        action = str(audit.get("action") or "")
        after_status = str(audit.get("after_status") or "")
        if action in ACTION_STRENGTHENING:
            strengthened.append(variable)
        if action in ACTION_WEAKENING:
            weakened.append(variable)
        if action == "request_better_source" or after_status == "needs_better_source":
            needs_better.append(variable)
        if after_status in {"rejected_evidence", "marked_noise"}:
            inactive_evidence_ids.append(evidence_id)
        rows.append(
            {
                "evidence_id": evidence_id,
                "action": action,
                "variable": variable,
                "before_lifecycle_status": audit.get("before_status"),
                "after_lifecycle_status": after_status,
                "before_allowed_usage": audit.get("before_allowed_usage"),
                "after_allowed_usage": audit.get("after_allowed_usage"),
                "promotion_allowed_after_action": bool(audit.get("promotion_allowed_after_action")),
                "reviewed_at": audit.get("created_at"),
            }
        )
    changed = set(strengthened) | set(weakened) | set(needs_better)
    return {
        "strengthened_variables": sorted(set(strengthened)),
        "weakened_variables": sorted(set(weakened)),
        "needs_better_source_variables": sorted(set(needs_better)),
        "unchanged_variables": [item for item in VARIABLE_SCOPE if item not in changed],
        "inactive_evidence_ids": inactive_evidence_ids,
        "reviewed_rows": rows,
    }


def _safe_variable_packs(conn: sqlite3.Connection, ticker: str) -> dict[str, Any]:
    try:
        return build_variable_evidence_packs(conn, ticker)
    except Exception as exc:  # pragma: no cover - defensive for partial local DBs.
        return {
            "supplier_share": {"evidence_status": "missing", "missing_reason": str(exc)},
            "ASP_price_proxy": {"evidence_status": "missing", "missing_reason": str(exc)},
            "capacity": {"evidence_status": "missing", "missing_reason": str(exc)},
            "customer_allocation_proxy": {"evidence_status": "missing", "missing_reason": str(exc)},
            "consensus": {"evidence_status": "missing", "official_consensus_available": False, "missing_reason": str(exc)},
        }


def _remaining_core_gaps(packs: dict[str, Any]) -> list[str]:
    gaps: list[str] = []
    for variable in ("supplier_share", "ASP_price_proxy", "customer_allocation_proxy"):
        status = str((packs.get(variable) or {}).get("evidence_status") or "missing")
        if status != "confirmed":
            gaps.append(variable)
    consensus = packs.get("consensus") or {}
    if not consensus.get("official_consensus_available"):
        gaps.append("official_consensus")
    return gaps


def _active_linked_count(candidates: list[dict[str, Any]], states: dict[str, dict[str, Any]]) -> int:
    count = 0
    for candidate in candidates:
        evidence_id = str(candidate.get("evidence_id") or "")
        state = states.get(evidence_id) or {}
        if str(state.get("lifecycle_status") or "") in INACTIVE_LIFECYCLE_STATUSES:
            continue
        if normalize_research_variable(candidate.get("variable_type")) in set(VARIABLE_SCOPE) | set(CORE_GAP_VARIABLES):
            count += 1
    return count


def build_post_governance_evidence_state(
    conn: sqlite3.Connection,
    *,
    ticker: str | None = None,
    tickers: str | None = None,
) -> dict[str, Any]:
    """Aggregate Phase 33 evidence governance state by ticker."""

    resolved = resolve_phase34_tickers(ticker, tickers)
    all_audits = [row for row in phase33_audits(conn) if not resolved or row.get("ticker") in set(resolved)]
    candidates = _candidate_by_id(conn)
    states = _state_by_id(conn)
    repair_tasks = [task for task in list_download_repair_tasks(conn) if not resolved or task.get("ticker") in set(resolved)]
    audits_by_ticker: dict[str, list[dict[str, Any]]] = defaultdict(list)
    candidates_by_ticker: dict[str, list[dict[str, Any]]] = defaultdict(list)
    repairs_by_ticker: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in all_audits:
        audits_by_ticker[str(row.get("ticker") or "UNKNOWN")].append(row)
    for row in candidates.values():
        candidates_by_ticker[str(row.get("ticker") or "UNKNOWN")].append(row)
    for task in repair_tasks:
        repairs_by_ticker[str(task.get("ticker") or "UNKNOWN")].append(task)

    ticker_results: list[dict[str, Any]] = []
    for item in resolved:
        ticker_audits = audits_by_ticker.get(item, [])
        ticker_candidates = candidates_by_ticker.get(item, [])
        action_counts = _action_counts(ticker_audits)
        after_counts = _after_counts(ticker_audits)
        packs = _safe_variable_packs(conn, item)
        changes = _variable_changes(ticker_audits, candidates, states)
        evidence_state = {
            "total_semantic_evidence": len(ticker_candidates),
            "reviewed_evidence": len(_reviewed_ids(ticker_audits)),
            "approved_evidence": after_counts.get("approved_evidence", 0),
            "rejected_evidence": after_counts.get("rejected_evidence", 0),
            "downgraded_evidence": after_counts.get("downgraded_evidence", 0),
            "marked_noise": after_counts.get("marked_noise", 0),
            "needs_better_source": after_counts.get("needs_better_source", 0),
            "linked_to_variable_pack": _active_linked_count(ticker_candidates, states),
            "active_semantic_evidence": sum(
                1
                for candidate in ticker_candidates
                if str((states.get(str(candidate.get("evidence_id"))) or {}).get("lifecycle_status") or "")
                not in INACTIVE_LIFECYCLE_STATUSES
            ),
        }
        ticker_results.append(
            {
                "ticker": item,
                "company_name": COMPANY_NAMES.get(item),
                "evidence_state": evidence_state,
                "evidence_delta": changes,
                "actions_by_type": dict(action_counts),
                "repair_tasks": repairs_by_ticker.get(item, []),
                "repair_tasks_open": sum(1 for task in repairs_by_ticker.get(item, []) if task.get("status") == "open"),
                "remaining_core_gaps": _remaining_core_gaps(packs),
                "variable_pack_snapshot": {
                    "supplier_share": (packs.get("supplier_share") or {}).get("evidence_status"),
                    "ASP_price_proxy": (packs.get("ASP_price_proxy") or {}).get("evidence_status"),
                    "capacity": (packs.get("capacity") or {}).get("evidence_status"),
                    "customer_allocation_proxy": (packs.get("customer_allocation_proxy") or {}).get("evidence_status"),
                    "official_consensus": "available" if (packs.get("consensus") or {}).get("official_consensus_available") else "missing",
                },
            }
        )

    after_counts = _after_counts(all_audits)
    summary = {
        "tickers_checked": len(ticker_results),
        "reviewed_evidence": len(_reviewed_ids(all_audits)),
        "approved_evidence": after_counts.get("approved_evidence", 0),
        "rejected_evidence": after_counts.get("rejected_evidence", 0),
        "downgraded_evidence": after_counts.get("downgraded_evidence", 0),
        "marked_noise": after_counts.get("marked_noise", 0),
        "needs_better_source": after_counts.get("needs_better_source", 0),
        "repair_tasks_open": sum(1 for task in repair_tasks if task.get("status") == "open"),
        "promotion_allowed_true": sum(1 for row in all_audits if row.get("promotion_allowed_after_action")),
        "new_pending_created": 0,
        "paper_order_created": 0,
    }
    return {
        "generated_at": now_ts(),
        "summary": summary,
        "ticker_results": ticker_results,
        "safety": {
            "read_only_revalidation": True,
            "approved_evidence_is_promotion_evidence": False,
            "promotion_rules_relaxed": False,
            "new_pending_created": 0,
            "paper_order_created": 0,
            "real_trade_risk": False,
        },
    }


def _status_for_variable(packs: dict[str, Any], variable: str) -> str:
    if variable == "consensus_expectation_proxy":
        return str((packs.get("consensus") or {}).get("evidence_status") or "missing")
    if variable == "official_consensus":
        return "confirmed" if (packs.get("consensus") or {}).get("official_consensus_available") else "missing"
    if variable == "shipment":
        return str((packs.get("capacity") or {}).get("evidence_status") or "missing")
    if variable in {"industry_forecast", "product_exposure", "margin_signal", "order_visibility"}:
        return "context_only"
    return str((packs.get(variable) or {}).get("evidence_status") or "missing")


def build_variable_pack_post_governance(
    conn: sqlite3.Connection,
    *,
    ticker: str | None = None,
    tickers: str | None = None,
) -> dict[str, Any]:
    evidence = build_post_governance_evidence_state(conn, ticker=ticker, tickers=tickers)
    rows: list[dict[str, Any]] = []
    strengthened = weakened = unchanged = 0
    for ticker_row in evidence.get("ticker_results") or []:
        item = str(ticker_row.get("ticker"))
        packs = _safe_variable_packs(conn, item)
        delta = ticker_row.get("evidence_delta") or {}
        strength_set = set(delta.get("strengthened_variables") or [])
        weak_set = set(delta.get("weakened_variables") or [])
        variable_rows: list[dict[str, Any]] = []
        for variable in VARIABLE_SCOPE:
            before = _status_for_variable(packs, variable)
            after = before
            change = "unchanged"
            reason = "no reviewed evidence changed this variable"
            if variable in weak_set:
                change = "weakened"
                after = "context_only" if before not in {"blocked", "missing"} else before
                reason = "reviewed evidence was downgraded, rejected, noisy, or needs a better source"
                weakened += 1
            elif variable in strength_set:
                change = "strengthened_with_reviewed_evidence"
                after = "partial" if before in {"missing", "context_only", "planned_only"} else before
                reason = "approved evidence supports the variable but remains non-confirmed semantic evidence"
                strengthened += 1
            else:
                unchanged += 1
            variable_rows.append(
                {
                    "variable": variable,
                    "before_status": before,
                    "after_status": after,
                    "delta": change,
                    "reason": reason,
                    "confirmed_after": False,
                }
            )
        rows.append(
            {
                "ticker": item,
                "company_name": ticker_row.get("company_name"),
                "variable_pack_delta": variable_rows,
                "remaining_core_gaps": ticker_row.get("remaining_core_gaps") or list(CORE_GAP_VARIABLES),
            }
        )
    summary = {
        "tickers_checked": len(rows),
        "variable_packs_checked": sum(len(row.get("variable_pack_delta") or []) for row in rows),
        "variables_strengthened": strengthened,
        "variables_weakened": weakened,
        "variables_unchanged": unchanged,
        "confirmed_variables_added": 0,
        "new_pending_created": 0,
    }
    return {
        "generated_at": now_ts(),
        "overall_status": "partial_pass" if strengthened or weakened else "pass",
        "summary": summary,
        "ticker_results": rows,
        "safety": {
            "confirmed_supplier_share_added": 0,
            "confirmed_ASP_added": 0,
            "confirmed_customer_allocation_added": 0,
            "official_consensus_added": 0,
            "promotion_rules_relaxed": False,
        },
    }


def build_expectation_gap_post_governance(
    conn: sqlite3.Connection,
    *,
    ticker: str | None = None,
    tickers: str | None = None,
) -> dict[str, Any]:
    evidence = build_post_governance_evidence_state(conn, ticker=ticker, tickers=tickers)
    rows: list[dict[str, Any]] = []
    gap_weakened = gap_unchanged = confidence_downgraded = 0
    for ticker_row in evidence.get("ticker_results") or []:
        item = str(ticker_row.get("ticker"))
        packs = _safe_variable_packs(conn, item)
        try:
            before_gap = (build_expectation_gap(conn, item, variable_evidence=packs).get("expectation_gap") or {})
        except Exception:
            before_gap = {"status": "insufficient_data", "confidence": "low", "score": 0}
        evidence_state = ticker_row.get("evidence_state") or {}
        weak_count = int(evidence_state.get("rejected_evidence") or 0) + int(evidence_state.get("marked_noise") or 0) + int(evidence_state.get("downgraded_evidence") or 0)
        delta = "weakened" if weak_count and evidence_state.get("reviewed_evidence") else "unchanged"
        after_confidence = before_gap.get("confidence")
        if delta == "weakened":
            gap_weakened += 1
            if before_gap.get("confidence") in {"medium", "low_to_medium"}:
                after_confidence = "low"
                confidence_downgraded += 1
        else:
            gap_unchanged += 1
        rows.append(
            {
                "ticker": item,
                "before": {
                    "expectation_gap_status": before_gap.get("status"),
                    "confidence": before_gap.get("confidence"),
                },
                "after": {
                    "expectation_gap_status": before_gap.get("status"),
                    "confidence": after_confidence,
                },
                "delta": delta,
                "why_not_upgraded": [
                    "supplier share still not disclosed",
                    "ASP still missing",
                    "customer allocation still missing",
                    "official consensus missing",
                ],
                "why_not_downgraded": ["supportive context evidence remains, but not enough to raise confidence"] if delta == "unchanged" else [],
            }
        )
    summary = {
        "tickers_checked": len(rows),
        "gap_strengthened": 0,
        "gap_weakened": gap_weakened,
        "gap_unchanged": gap_unchanged,
        "confidence_upgraded": 0,
        "confidence_downgraded": confidence_downgraded,
        "new_pending_created": 0,
    }
    return {
        "generated_at": now_ts(),
        "overall_status": "partial_pass",
        "summary": summary,
        "ticker_results": rows,
        "safety": {
            "expectation_gap_auto_pending": False,
            "confidence_forced_high": False,
            "new_pending_created": 0,
        },
    }


def build_valuation_support_post_governance(
    conn: sqlite3.Connection,
    *,
    ticker: str | None = None,
    tickers: str | None = None,
) -> dict[str, Any]:
    evidence = build_post_governance_evidence_state(conn, ticker=ticker, tickers=tickers)
    rows: list[dict[str, Any]] = []
    weakened = unchanged = 0
    for ticker_row in evidence.get("ticker_results") or []:
        state = ticker_row.get("evidence_state") or {}
        weak_count = int(state.get("rejected_evidence") or 0) + int(state.get("marked_noise") or 0) + int(state.get("downgraded_evidence") or 0)
        delta = "weakened" if weak_count and state.get("reviewed_evidence") else "unchanged"
        weakened += int(delta == "weakened")
        unchanged += int(delta == "unchanged")
        rows.append(
            {
                "ticker": ticker_row.get("ticker"),
                "valuation_support_before": "context_only",
                "valuation_support_after": "context_only",
                "delta": delta,
                "remaining_blockers": ["ASP missing", "official consensus missing", "supplier share missing"],
            }
        )
    return {
        "generated_at": now_ts(),
        "overall_status": "partial_pass",
        "summary": {
            "tickers_checked": len(rows),
            "valuation_support_improved": 0,
            "valuation_support_weakened": weakened,
            "valuation_support_unchanged": unchanged,
            "valuation_gate_promoted": 0,
            "new_pending_created": 0,
        },
        "ticker_results": rows,
        "safety": {
            "semantic_evidence_replaces_valuation": False,
            "official_consensus_fabricated": False,
            "valuation_gate_promoted": 0,
            "promotion_rules_relaxed": False,
        },
    }


def build_bear_case_post_governance(
    conn: sqlite3.Connection,
    *,
    ticker: str | None = None,
    tickers: str | None = None,
) -> dict[str, Any]:
    evidence = build_post_governance_evidence_state(conn, ticker=ticker, tickers=tickers)
    rows: list[dict[str, Any]] = []
    worsened = unchanged = 0
    for ticker_row in evidence.get("ticker_results") or []:
        state = ticker_row.get("evidence_state") or {}
        weak_count = int(state.get("rejected_evidence") or 0) + int(state.get("marked_noise") or 0) + int(state.get("downgraded_evidence") or 0)
        delta = "worsened" if weak_count and state.get("reviewed_evidence") else "unchanged"
        worsened += int(delta == "worsened")
        unchanged += int(delta == "unchanged")
        rows.append(
            {
                "ticker": ticker_row.get("ticker"),
                "bear_case_before": "partially_mitigated",
                "bear_case_after": "partially_mitigated",
                "delta": delta,
                "remaining_bear_points": [
                    "customer allocation unconfirmed",
                    "ASP missing",
                    "supplier share missing",
                ],
                "blocks_pending_after_review": True,
            }
        )
    return {
        "generated_at": now_ts(),
        "overall_status": "partial_pass",
        "summary": {
            "tickers_checked": len(rows),
            "bear_case_mitigated": 0,
            "bear_case_worsened": worsened,
            "bear_case_unchanged": unchanged,
            "blocks_pending_after_review": len(rows),
        },
        "ticker_results": rows,
        "safety": {
            "bear_case_change_triggers_promotion": False,
            "promotion_rules_relaxed": False,
        },
    }


def safe_next_evidence_plan_for_ticker(ticker_row: dict[str, Any]) -> list[dict[str, Any]]:
    gaps = set(ticker_row.get("remaining_core_gaps") or CORE_GAP_VARIABLES)
    plan: list[dict[str, Any]] = []
    templates = {
        "ASP_price_proxy": (
            "ASP_PRICE_EVIDENCE_NEEDED",
            "ASP missing prevents valuation support upgrade",
            ["company IR", "authorized industry forecast source", "public price commentary"],
            "valuation_support",
        ),
        "supplier_share": (
            "SUPPLIER_SHARE_EVIDENCE_NEEDED",
            "supplier share remains undisclosed; do not fabricate confirmed share",
            ["company IR", "authorized industry source", "public customer/supplier disclosure"],
            "scenario_analysis_only",
        ),
        "customer_allocation_proxy": (
            "CUSTOMER_ALLOCATION_EVIDENCE_NEEDED",
            "customer allocation remains unconfirmed; do not fabricate confirmed customer allocation",
            ["company IR", "authorized industry source", "customer-side public statement"],
            "scenario_analysis_only",
        ),
        "official_consensus": (
            "OFFICIAL_CONSENSUS_NEEDED",
            "internal proxy cannot be treated as official consensus",
            ["commercial consensus provider", "authorized sell-side estimate source"],
            "valuation_support",
        ),
    }
    for variable in CORE_GAP_VARIABLES:
        if variable not in gaps:
            continue
        plan_type, reason, sources, usage = templates[variable]
        plan.append(
            {
                "plan_type": plan_type,
                "priority": "high",
                "reason": reason,
                "suggested_sources": sources,
                "allowed_usage_target": usage,
            }
        )
    if (ticker_row.get("evidence_state") or {}).get("needs_better_source"):
        plan.append(
            {
                "plan_type": "BETTER_SOURCE_NEEDED",
                "priority": "medium",
                "reason": "at least one reviewed evidence item needs a better source",
                "suggested_sources": ["clean company IR text", "authorized public filing", "non-restricted public source"],
                "allowed_usage_target": "context_only",
            }
        )
    if ticker_row.get("repair_tasks_open"):
        plan.append(
            {
                "plan_type": "DOWNLOAD_REPAIR_NEEDED",
                "priority": "medium",
                "reason": "download repair queue has open source tasks",
                "suggested_sources": ["manual clean text if legally available", "alternate official source URL"],
                "allowed_usage_target": "planned_only",
            }
        )
    return plan


def build_next_evidence_plan(
    conn: sqlite3.Connection,
    *,
    ticker: str | None = None,
    tickers: str | None = None,
) -> dict[str, Any]:
    evidence = build_post_governance_evidence_state(conn, ticker=ticker, tickers=tickers)
    rows = []
    for ticker_row in evidence.get("ticker_results") or []:
        rows.append({"ticker": ticker_row.get("ticker"), "plan_items": safe_next_evidence_plan_for_ticker(ticker_row)})
    plan_count = sum(len(row.get("plan_items") or []) for row in rows)
    high_count = sum(1 for row in rows for item in row.get("plan_items") or [] if item.get("priority") == "high")
    return {
        "generated_at": now_ts(),
        "summary": {
            "tickers_checked": len(rows),
            "evidence_plan_items": plan_count,
            "high_priority_plan_items": high_count,
            "repair_queue_items": (evidence.get("summary") or {}).get("repair_tasks_open", 0),
        },
        "ticker_results": rows,
        "safety": {
            "plan_only_no_evidence_written": True,
            "illegal_source_recommended": False,
            "confirmed_sensitive_variable_fabricated": False,
        },
    }
