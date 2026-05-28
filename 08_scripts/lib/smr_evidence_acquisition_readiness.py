#!/usr/bin/env python3
"""Phase 36 readiness scoring for evidence acquisition tasks."""

from __future__ import annotations

import sqlite3
from typing import Any

from smr_evidence_acquisition_task import build_evidence_acquisition_tasks
from smr_wiki import now_ts


IMPACT = {
    "ASP_price_proxy": 28,
    "customer_allocation_proxy": 27,
    "official_consensus": 24,
    "supplier_share": 30,
    "shipment": 20,
    "order_visibility": 20,
    "industry_forecast": 16,
    "margin_signal": 15,
    "product_exposure": 12,
}
FEASIBILITY_BY_TASK = {
    "FIND_COMPANY_IR_EVIDENCE": 24,
    "FIND_ANNUAL_REPORT_EVIDENCE": 20,
    "FIND_EXCHANGE_INTERACTION_EVIDENCE": 20,
    "FIND_INDUSTRY_FORECAST_EVIDENCE": 18,
    "FIND_CUSTOMER_SIDE_PUBLIC_SIGNAL": 12,
    "FIND_OFFICIAL_CONSENSUS_SOURCE": 12,
    "MANUAL_RESEARCH_REQUIRED": 8,
    "MARK_NOT_PUBLICLY_CONFIRMABLE": 6,
    "REPAIR_EVIDENCE_CHAIN": 18,
}
QUALITY_BY_TASK = {
    "FIND_COMPANY_IR_EVIDENCE": 18,
    "FIND_ANNUAL_REPORT_EVIDENCE": 18,
    "FIND_EXCHANGE_INTERACTION_EVIDENCE": 16,
    "FIND_INDUSTRY_FORECAST_EVIDENCE": 12,
    "FIND_CUSTOMER_SIDE_PUBLIC_SIGNAL": 12,
    "FIND_OFFICIAL_CONSENSUS_SOURCE": 20,
    "MANUAL_RESEARCH_REQUIRED": 8,
    "MARK_NOT_PUBLICLY_CONFIRMABLE": 5,
}
SAFETY_PENALTY = {"supplier_share": 18, "customer_allocation_proxy": 28, "official_consensus": 10}


def _bucket(score: int) -> str:
    if score >= 72:
        return "high_priority"
    if score >= 55:
        return "medium_priority"
    return "manual_or_low_confidence"


def _reason(task: dict[str, Any], score: int) -> str:
    variable = task.get("variable")
    task_type = task.get("task_type")
    if variable == "ASP_price_proxy" and task_type == "FIND_COMPANY_IR_EVIDENCE":
        return "high impact, feasible via company IR, improves valuation support"
    if variable in {"supplier_share", "customer_allocation_proxy"}:
        return "high impact but low public availability and high safety caveat burden"
    if variable == "official_consensus":
        return "useful for valuation support but dependent on authorized provider access"
    return f"score reflects research impact, feasibility, expected quality, safety risk, and time cost ({score})"


def score_task(task: dict[str, Any]) -> dict[str, Any]:
    variable = str(task.get("variable") or "")
    task_type = str(task.get("task_type") or "")
    impact = IMPACT.get(variable, 10)
    feasibility = FEASIBILITY_BY_TASK.get(task_type, 10)
    quality = QUALITY_BY_TASK.get(task_type, 10)
    source_availability = feasibility
    safety_risk = SAFETY_PENALTY.get(variable, 4)
    time_cost_penalty = 4 if task_type in {"FIND_COMPANY_IR_EVIDENCE", "FIND_ANNUAL_REPORT_EVIDENCE"} else 8
    score = max(0, min(100, impact + feasibility + quality + source_availability - safety_risk - time_cost_penalty))
    return {
        "task_id": task.get("task_id"),
        "variable": variable,
        "task_type": task_type,
        "readiness_score": score,
        "readiness_bucket": _bucket(score),
        "reason": _reason(task, score),
        "dimensions": {
            "impact_on_research": impact,
            "feasibility": feasibility,
            "source_availability": source_availability,
            "expected_quality": quality,
            "safety_risk_penalty": safety_risk,
            "time_cost_penalty": time_cost_penalty,
        },
    }


def build_acquisition_readiness_score(conn: sqlite3.Connection, ticker: str) -> dict[str, Any]:
    tasks_payload = build_evidence_acquisition_tasks(conn, ticker)
    scored = [score_task(task) for task in tasks_payload.get("evidence_acquisition_tasks") or []]
    scored = sorted(scored, key=lambda row: (-int(row.get("readiness_score") or 0), str(row.get("task_id") or "")))
    return {
        "generated_at": now_ts(),
        "ticker": tasks_payload.get("ticker"),
        "company_name": tasks_payload.get("company_name"),
        "acquisition_readiness": scored,
        "summary": {
            "tasks_scored": len(scored),
            "high_priority": sum(1 for row in scored if row.get("readiness_bucket") == "high_priority"),
            "manual_or_low_confidence": sum(1 for row in scored if row.get("readiness_bucket") == "manual_or_low_confidence"),
        },
        "safety": {
            "readiness_is_investment_rating": False,
            "fetch_executed": False,
            "evidence_written": False,
            "new_pending_created": 0,
        },
    }
