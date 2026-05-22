#!/usr/bin/env python3
"""Structured recommendation candidate builder.

Report text may describe a thesis, but this module decides the machine-readable
candidate action from structured gates: promotion, evidence, valuation, proxy,
bear case, risk, and market signal.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime
from typing import Any

from smr_decision import upsert_decision_ledger
from smr_recommendation_promotion import PromotionResult, promotion_to_dict
from smr_portfolio_risk import evaluate_portfolio_risk


def _now_id() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S%f")


def _quality(proxy: dict[str, Any]) -> str:
    return str(proxy.get("proxy_quality") or "invalid").lower()


def _valuation_usage(valuation: dict[str, Any]) -> str:
    return str(valuation.get("allowed_usage") or "context_only").lower()


def _bear_strength(bear_case: dict[str, Any]) -> str:
    return str(bear_case.get("bear_case_strength") or "medium").lower()


def _risk_blocked(risk_snapshot: dict[str, Any]) -> bool:
    status = str(risk_snapshot.get("status") or risk_snapshot.get("risk_status") or "pass").lower()
    return status in {"block", "blocked"} or bool(risk_snapshot.get("liquidity_block"))


def _market_signal_positive(market_signal: dict[str, Any]) -> bool:
    signal = str(market_signal.get("signal") or market_signal.get("direction") or market_signal.get("status") or "").lower()
    return signal in {"positive", "bullish", "up", "pass", "allowed"}


def decide_action(
    promotion_result: dict[str, Any],
    valuation_snapshot: dict[str, Any],
    consensus_proxy: dict[str, Any],
    bear_case: dict[str, Any],
    risk_snapshot: dict[str, Any],
    market_signal: dict[str, Any],
    portfolio_risk: dict[str, Any] | None = None,
) -> tuple[str, list[str], float, float, float]:
    reasons: list[str] = []
    confidence = 0.35
    suggested_position_pct = 0.0
    max_position_pct = 0.0
    portfolio_risk = portfolio_risk or {}
    if not promotion_result.get("allowed"):
        missing = promotion_result.get("missing_requirements") or []
        reasons.append("promotion_not_allowed")
        reasons.extend(f"missing:{item}" for item in missing[:6])
        if _valuation_usage(valuation_snapshot) == "context_only" or _quality(consensus_proxy) in {"weak", "invalid"}:
            return "observation", reasons, confidence, suggested_position_pct, max_position_pct
        return "watch", reasons, confidence, suggested_position_pct, max_position_pct

    action = "small_candidate"
    confidence = 0.58
    suggested_position_pct = 1.0
    max_position_pct = 3.0
    valuation_usage = _valuation_usage(valuation_snapshot)
    proxy_quality = _quality(consensus_proxy)
    bear_strength = _bear_strength(bear_case)

    if valuation_usage == "context_only":
        reasons.append("valuation_context_only_caps_action")
        return "watch", reasons, 0.42, 0.0, 0.0
    if valuation_usage == "blocked_due_to_stale_price":
        reasons.append("valuation_stale_price_blocks_action")
        return "observation", reasons, 0.35, 0.0, 0.0
    if proxy_quality in {"weak", "invalid"}:
        reasons.append("proxy_not_strong_enough")
        return "watch", reasons, 0.45, 0.0, 0.0
    if proxy_quality == "strong":
        confidence += 0.08
    if valuation_usage == "promotion_eligible":
        confidence += 0.08
        action = "buy_candidate"
        suggested_position_pct = 2.0
        max_position_pct = 5.0
    elif valuation_usage == "supporting_evidence":
        confidence += 0.04
        action = "small_candidate"
        suggested_position_pct = 1.5
        max_position_pct = 4.0
    if _market_signal_positive(market_signal):
        confidence += 0.04
    if _risk_blocked(risk_snapshot):
        reasons.append("risk_blocked")
        return "observation", reasons, min(confidence, 0.4), 0.0, 0.0
    risk_status = str(portfolio_risk.get("status") or "pass").lower()
    risk_action = str(portfolio_risk.get("recommended_action") or "").lower()
    if risk_status == "block":
        reasons.append("portfolio_risk_blocked")
        if portfolio_risk.get("blocking_factors"):
            reasons.extend(
                f"{item.get('code')}: {item.get('detail')}"
                for item in portfolio_risk.get("blocking_factors")[:4]
                if isinstance(item, dict)
            )
        return "observation", reasons, min(confidence, 0.35), 0.0, 0.0
    if risk_status == "warn":
        reasons.append("portfolio_risk_downsizes_candidate")
        if risk_action == "downsize":
            action = "small_candidate" if action == "buy_candidate" else action
        suggested_position_pct = min(suggested_position_pct, float(portfolio_risk.get("recommended_position_pct") or suggested_position_pct))
        max_position_pct = min(max_position_pct, float(portfolio_risk.get("recommended_max_position_pct") or max_position_pct))
    if bear_strength == "high":
        reasons.append("high_bear_case_reduces_action")
        action = "small_candidate" if action == "buy_candidate" else "watch"
        suggested_position_pct = min(suggested_position_pct, 1.0)
        max_position_pct = min(max_position_pct, 2.0)
        confidence -= 0.08
    return action, reasons or ["structured_gates_passed"], round(max(min(confidence, 0.85), 0.0), 2), suggested_position_pct, max_position_pct


def build_recommendation_candidate(
    conn: sqlite3.Connection | None = None,
    recommendation_id: str | None = None,
    ticker: str | None = None,
    report: dict[str, Any] | None = None,
    claim_graph: dict[str, Any] | None = None,
    evidence_check: dict[str, Any] | None = None,
    valuation_snapshot: dict[str, Any] | None = None,
    consensus_proxy: dict[str, Any] | None = None,
    bear_case: dict[str, Any] | None = None,
    risk_snapshot: dict[str, Any] | None = None,
    portfolio_risk: dict[str, Any] | None = None,
    market_signal: dict[str, Any] | None = None,
    promotion_result: PromotionResult | dict[str, Any] | None = None,
    write_ledger: bool = False,
) -> dict[str, Any]:
    report = report or {}
    claim_graph = claim_graph or {}
    evidence_check = evidence_check or {}
    valuation_snapshot = valuation_snapshot or {}
    consensus_proxy = consensus_proxy or {}
    bear_case = bear_case or {}
    risk_snapshot = risk_snapshot or {}
    portfolio_risk = portfolio_risk or {}
    market_signal = market_signal or {}
    promotion = promotion_to_dict(promotion_result)
    rec_id = recommendation_id or f"rec_candidate_{_now_id()}"
    ticker = ticker or report.get("ticker") or valuation_snapshot.get("ticker") or consensus_proxy.get("ticker")
    action, action_reasons, confidence, suggested_position_pct, max_position_pct = decide_action(
        promotion,
        valuation_snapshot,
        consensus_proxy,
        bear_case,
        risk_snapshot,
        market_signal,
        portfolio_risk,
    )
    if promotion.get("allowed") and action not in {"watch", "observation"}:
        status = "pending_human_review"
    elif action == "watch":
        status = "candidate_shadow"
    else:
        status = "observation_only"
    kill_conditions = list(bear_case.get("deal_breakers") or report.get("kill_conditions") or [])
    candidate = {
        "recommendation_id": rec_id,
        "ticker": ticker,
        "action": action,
        "confidence": confidence,
        "suggested_position_pct": suggested_position_pct,
        "max_position_pct": max_position_pct,
        "time_horizon": report.get("time_horizon") or "3-6 months",
        "entry_conditions": report.get("entry_conditions") or [],
        "add_conditions": report.get("add_conditions") or [],
        "reduce_conditions": report.get("reduce_conditions") or [],
        "kill_conditions": kill_conditions,
        "status": status,
        "reasons": action_reasons,
        "snapshots": {
            "claim_graph": claim_graph,
            "evidence_check": evidence_check,
            "valuation_snapshot": valuation_snapshot,
            "consensus_proxy": consensus_proxy,
            "bear_case": bear_case,
            "risk_snapshot": risk_snapshot,
            "portfolio_risk": portfolio_risk,
            "market_signal": market_signal,
            "promotion_result": promotion,
        },
    }
    if write_ledger and conn is not None:
        market = valuation_snapshot.get("market") or consensus_proxy.get("market")
        upsert_decision_ledger(
            conn,
            recommendation_id=rec_id,
            status=status,
            dashboard_summary={
                "action": action,
                "ticker": ticker,
                "suggested_position_pct": suggested_position_pct,
                "max_position_pct": max_position_pct,
                "kill_triggers": kill_conditions,
                "confidence_rationale": "; ".join(action_reasons),
                "valuation_snapshot": valuation_snapshot,
            },
            evidence_check_snapshot=evidence_check,
            lint_snapshot={},
            risk_snapshot=risk_snapshot,
            metadata={
                "ticker": ticker,
                "market": market,
                "candidate": candidate,
                "promotion_result": promotion,
                "claim_graph": claim_graph,
                "consensus_proxy": consensus_proxy,
                "bear_case": bear_case,
            },
        )
    return candidate


def candidate_to_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    return json.loads(json.dumps(value, ensure_ascii=False, default=str))
