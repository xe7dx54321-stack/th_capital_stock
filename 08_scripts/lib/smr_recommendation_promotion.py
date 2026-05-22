#!/usr/bin/env python3
"""Deterministic promotion rules for auditable recommendation candidates."""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict, dataclass
from typing import Any

from smr_decision import upsert_decision_ledger


@dataclass
class PromotionResult:
    from_status: str
    to_status: str
    allowed: bool
    reasons: list[str]
    missing_requirements: list[str]
    required_fixes: list[str]
    snapshots: dict[str, Any]


def _asdict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    try:
        return json.loads(json.dumps(value, ensure_ascii=False, default=str))
    except TypeError:
        return {}


def _action_text(summary: dict[str, Any], candidate: dict[str, Any]) -> str:
    return " ".join(
        str(value or "")
        for value in (
            summary.get("action"),
            summary.get("action_detail"),
            candidate.get("action"),
        )
    ).lower()


def is_buy_or_add(action: str) -> bool:
    return any(token in action for token in ("buy", "add", "small_candidate", "buy_candidate", "买入", "加仓", "调入"))


def data_health_requirements(
    data_health: dict[str, Any],
    ticker: str | None,
    action: str,
) -> tuple[list[str], list[str], list[str]]:
    reasons: list[str] = []
    missing: list[str] = []
    fixes: list[str] = []
    rows = data_health.get("items") or []
    if not rows:
        missing.append("data_health_snapshot")
        fixes.append("run recompute_data_source_health.py after news/filings ingestion")
        return reasons, missing, fixes
    blocking_rows = [row for row in rows if row.get("blocking_level") == "block"]
    if blocking_rows:
        reasons.append("data_health has block-level source issue")
        missing.append("no_block_level_source_issue")
        fixes.append("repair block-level data sources before promotion")
    daily_rows = [row for row in rows if row.get("data_type") == "daily_bar"]
    if not daily_rows or any(row.get("freshness_status") not in {"fresh"} for row in daily_rows):
        missing.append("daily_bar_fresh")
        fixes.append("backfill A/H/US daily_bar to expected latest trading day")
    news_rows = [row for row in rows if row.get("data_type") == "news"]
    if not news_rows:
        missing.append("news_health")
        fixes.append("run ingest_news.py or recompute_news_health.py")
    elif all(row.get("freshness_status") in {"stale", "missing", "unknown"} for row in news_rows):
        missing.append("news_not_globally_stale")
        fixes.append("repair at least one active news source/market freshness")
    filing_rows = [row for row in rows if row.get("data_type") == "filings"]
    relevant_filing_rows = [
        row for row in filing_rows
        if not ticker
        or str(row.get("metadata", {}).get("ticker") or "").upper() == ticker.upper()
        or str(row.get("metadata", {}).get("scope") or "") in {"watchlist", "market", "global"}
        or row.get("market") in {"watchlist", "global"}
    ]
    if is_buy_or_add(action):
        if not relevant_filing_rows:
            missing.append("relevant_filings_health")
            fixes.append("run ingest_filings.py for watchlist/ticker and export filing evidence")
        elif all(row.get("freshness_status") in {"stale", "missing", "unknown"} for row in relevant_filing_rows):
            missing.append("relevant_filings_not_stale")
            fixes.append("repair ticker/watchlist filings freshness")
    return reasons, missing, fixes


def evidence_requirements(
    evidence_check: dict[str, Any],
    claim_graph: dict[str, Any],
    action: str,
    bear_case: dict[str, Any] | None = None,
) -> tuple[list[str], list[str], list[str]]:
    reasons: list[str] = []
    missing: list[str] = []
    fixes: list[str] = []
    unsupported = claim_graph.get("unsupported_core_claims") or evidence_check.get("unsupported_core_claims") or []
    if unsupported:
        missing.append("all_core_claims_supported")
        fixes.append("link every core claim to evidence_id before promotion")
    low_quality = claim_graph.get("low_quality_core_claims") or evidence_check.get("low_quality_core_claims") or []
    if low_quality:
        missing.append("core_claim_evidence_quality")
        fixes.append("replace stale/low-quality evidence with primary or high-quality live evidence")
    summary = evidence_check.get("evidence_summary") or {}
    independent_count = (
        evidence_check.get("independent_source_count")
        or summary.get("independent_source_count")
        or summary.get("source_path_count")
        or 0
    )
    primary_count = (
        evidence_check.get("primary_evidence_count")
        or summary.get("primary_anchor_count")
        or summary.get("primary_source_count")
        or 0
    )
    if independent_count < 2:
        missing.append("two_independent_evidence_sources")
        fixes.append("add at least two independent evidence sources")
    if is_buy_or_add(action) and primary_count < 1:
        missing.append("primary_evidence_for_fundamental_claims")
        fixes.append("export filing/official IR evidence and link it to core company claims")
    counter_count = (
        claim_graph.get("counter_evidence_count")
        or evidence_check.get("counter_evidence_count")
        or len((bear_case or {}).get("bear_case_claims") or [])
        or 0
    )
    if is_buy_or_add(action) and counter_count < 1:
        missing.append("counter_evidence_or_bear_case_claim")
        fixes.append("add contradicts/contextual bear-case evidence before promotion")
    if evidence_check.get("severity") in {"block", "degrade"}:
        reasons.extend(evidence_check.get("reasons") or ["evidence checker did not pass"])
    return reasons, missing, fixes


def valuation_requirements(valuation: dict[str, Any], action: str) -> tuple[list[str], list[str], list[str]]:
    missing: list[str] = []
    fixes: list[str] = []
    if not valuation:
        missing.append("valuation_snapshot")
        fixes.append("run build_valuation_snapshot.py for the recommendation ticker")
        return [], missing, fixes
    allowed_usage = valuation.get("allowed_usage")
    if allowed_usage == "blocked_due_to_stale_price":
        missing.append("fresh_valuation_price")
        fixes.append("refresh daily_bar price before valuation can support action")
    if is_buy_or_add(action) and allowed_usage == "context_only":
        missing.append("valuation_not_context_only_for_buy_add")
        fixes.append("provide forward EPS proxy, historical percentile, or peer comparison")
    return [], missing, fixes


def fundamentals_requirements(fundamentals: dict[str, Any], action: str) -> tuple[list[str], list[str], list[str]]:
    if not is_buy_or_add(action):
        return [], [], []
    if not fundamentals:
        return (
            [],
            ["fundamentals_snapshot"],
            ["build ticker-level fundamentals_snapshot or mark strategy as event/technical-only"],
        )
    status = fundamentals.get("freshness_status")
    if status not in {"fresh", "degraded", "explainable_missing"}:
        return (
            [],
            ["fundamentals_snapshot_fresh_or_explainable"],
            ["refresh fundamentals_snapshot and expose missing_fields"],
        )
    if status == "degraded" and not fundamentals.get("missing_fields"):
        return (
            [],
            ["fundamentals_missing_fields_visible"],
            ["include fundamentals missing_fields before promotion"],
        )
    return [], [], []


def consensus_requirements(consensus_proxy: dict[str, Any], action: str) -> tuple[list[str], list[str], list[str]]:
    if not is_buy_or_add(action):
        return [], [], []
    official_active = bool(consensus_proxy.get("official_consensus_active") or consensus_proxy.get("is_official_consensus"))
    if official_active:
        return [], [], []
    quality = consensus_proxy.get("proxy_quality")
    usable = bool(consensus_proxy.get("usable_for_promotion"))
    if quality == "strong" and usable:
        return [], [], []
    if quality == "medium":
        return [], ["strong_proxy_or_official_consensus_for_pending_review"], ["add primary evidence or independent sources to upgrade proxy quality"]
    return [], ["consensus_proxy_quality"], ["build a strong internal proxy with linked evidence; do not present it as official consensus"]


def bear_case_requirements(bear_case: dict[str, Any], action: str) -> tuple[list[str], list[str], list[str]]:
    missing: list[str] = []
    fixes: list[str] = []
    if not is_buy_or_add(action):
        return [], missing, fixes
    claims = bear_case.get("bear_case_claims") or []
    deal_breakers = bear_case.get("deal_breakers") or []
    if not claims:
        missing.append("bear_case_claims")
        fixes.append("generate bear_case_claims for buy/add candidate")
    if not deal_breakers:
        missing.append("deal_breakers")
        fixes.append("write at least one deal breaker / kill condition")
    if bear_case.get("bear_case_strength") == "high" and not bear_case.get("thesis_response"):
        missing.append("high_bear_case_answered")
        fixes.append("answer high-strength bear case or downgrade to observation")
    if bear_case.get("data_quality_risk") == "high":
        missing.append("data_quality_risk_not_high")
        fixes.append("repair data quality risk before promotion")
    return [], missing, fixes


def risk_requirements(risk_snapshot: dict[str, Any], dashboard_summary: dict[str, Any], action: str) -> tuple[list[str], list[str], list[str]]:
    missing: list[str] = []
    fixes: list[str] = []
    status = str(risk_snapshot.get("status") or risk_snapshot.get("risk_status") or "pass").lower()
    if status in {"block", "blocked"} or risk_snapshot.get("liquidity_block"):
        missing.append("risk_snapshot_no_block")
        fixes.append("resolve risk/liquidity block before promotion")
    if is_buy_or_add(action):
        if dashboard_summary.get("suggested_position_pct") is None and not dashboard_summary.get("portfolio_action_plan"):
            missing.append("position_size")
            fixes.append("add suggested_position_pct or portfolio_action_plan")
        if dashboard_summary.get("max_position_pct") is None and not dashboard_summary.get("portfolio_action_plan"):
            missing.append("max_position")
            fixes.append("add max_position_pct or portfolio_action_plan")
    return [], missing, fixes


def lint_requirements(lint_result: dict[str, Any]) -> tuple[list[str], list[str], list[str]]:
    missing: list[str] = []
    fixes: list[str] = []
    issues = lint_result.get("issues") or []
    if lint_result.get("max_severity") in {"blocker", "error"}:
        missing.append("lint_no_blocker_or_error")
    for issue in issues:
        if issue.get("severity") in {"blocker", "error"} or issue.get("blocks_promotion"):
            missing.append(f"lint:{issue.get('code')}")
            if issue.get("required_fix") or issue.get("suggested_fix"):
                fixes.append(issue.get("required_fix") or issue.get("suggested_fix"))
    return [], missing, fixes


def evaluate_promotion(
    conn: sqlite3.Connection | None = None,
    report_id: str | None = None,
    recommendation_id: str | None = None,
    from_status: str = "observation_only",
    dashboard_summary: dict[str, Any] | None = None,
    data_health_snapshot: dict[str, Any] | None = None,
    evidence_check_snapshot: dict[str, Any] | None = None,
    claim_graph_snapshot: dict[str, Any] | None = None,
    valuation_snapshot: dict[str, Any] | None = None,
    consensus_proxy: dict[str, Any] | None = None,
    fundamentals_snapshot: dict[str, Any] | None = None,
    bear_case: dict[str, Any] | None = None,
    risk_snapshot: dict[str, Any] | None = None,
    lint_result: dict[str, Any] | None = None,
    write_ledger: bool = False,
) -> PromotionResult:
    summary = dashboard_summary or {}
    candidate = {}
    action = _action_text(summary, candidate)
    ticker = summary.get("ticker")
    missing: list[str] = []
    fixes: list[str] = []
    reasons: list[str] = []
    snapshots = {
        "report_id": report_id,
        "recommendation_id": recommendation_id,
        "dashboard_summary": summary,
        "data_health_snapshot": data_health_snapshot or {},
        "evidence_check_snapshot": evidence_check_snapshot or {},
        "claim_graph_snapshot": claim_graph_snapshot or {},
        "valuation_snapshot": valuation_snapshot or {},
        "consensus_proxy": consensus_proxy or {},
        "fundamentals_snapshot": fundamentals_snapshot or ((valuation_snapshot or {}).get("fundamentals_snapshot") or {}),
        "bear_case": bear_case or {},
        "risk_snapshot": risk_snapshot or {},
        "lint_result": lint_result or {},
    }
    for check in (
        data_health_requirements(data_health_snapshot or {}, ticker, action),
        evidence_requirements(evidence_check_snapshot or {}, claim_graph_snapshot or {}, action, bear_case or {}),
        valuation_requirements(valuation_snapshot or {}, action),
        fundamentals_requirements(
            fundamentals_snapshot or ((valuation_snapshot or {}).get("fundamentals_snapshot") or {}),
            action,
        ),
        consensus_requirements(consensus_proxy or {}, action),
        bear_case_requirements(bear_case or {}, action),
        risk_requirements(risk_snapshot or {}, summary, action),
        lint_requirements(lint_result or {}),
    ):
        check_reasons, check_missing, check_fixes = check
        reasons.extend(check_reasons)
        missing.extend(check_missing)
        fixes.extend(check_fixes)
    missing = list(dict.fromkeys(missing))
    fixes = list(dict.fromkeys(fixes))
    allowed = not missing
    if allowed:
        to_status = "pending_human_review"
        reasons.append("all promotion gates passed")
    elif not any(item.startswith("lint:") or item in {"daily_bar_fresh", "news_not_globally_stale", "relevant_filings_not_stale"} for item in missing):
        to_status = "candidate_shadow"
    else:
        to_status = from_status
    result = PromotionResult(
        from_status=from_status,
        to_status=to_status,
        allowed=allowed,
        reasons=reasons,
        missing_requirements=missing,
        required_fixes=fixes,
        snapshots=snapshots,
    )
    if allowed and write_ledger and conn is not None and recommendation_id:
        upsert_decision_ledger(
            conn,
            recommendation_id=recommendation_id,
            status="pending_human_review",
            dashboard_summary=summary,
            data_health_snapshot=data_health_snapshot,
            evidence_check_snapshot=evidence_check_snapshot,
            lint_snapshot=lint_result,
            risk_snapshot=risk_snapshot,
            metadata={
                "report_id": report_id,
                "promotion_result": asdict(result),
                "valuation_snapshot": valuation_snapshot,
                "consensus_proxy": consensus_proxy,
                "bear_case": bear_case,
            },
        )
    return result


def promotion_to_dict(result: PromotionResult | dict[str, Any] | None) -> dict[str, Any]:
    if result is None:
        return {}
    return _asdict(result)
