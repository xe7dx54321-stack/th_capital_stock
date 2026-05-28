#!/usr/bin/env python3
"""Phase 36 acquisition task builder."""

from __future__ import annotations

import hashlib
import sqlite3
from typing import Any

from smr_evidence_source_route_planner import build_evidence_source_routes
from smr_wiki import now_ts


ROUTE_TO_TASK_TYPE = {
    "company_ir": "FIND_COMPANY_IR_EVIDENCE",
    "investor_relations_record": "FIND_COMPANY_IR_EVIDENCE",
    "annual_report": "FIND_ANNUAL_REPORT_EVIDENCE",
    "semiannual_report": "FIND_ANNUAL_REPORT_EVIDENCE",
    "company_announcement": "FIND_ANNUAL_REPORT_EVIDENCE",
    "exchange_interaction": "FIND_EXCHANGE_INTERACTION_EVIDENCE",
    "industry_public_forecast": "FIND_INDUSTRY_FORECAST_EVIDENCE",
    "customer_side_public_signal": "FIND_CUSTOMER_SIDE_PUBLIC_SIGNAL",
    "official_consensus_provider": "FIND_OFFICIAL_CONSENSUS_SOURCE",
    "authorized_sell_side_source": "FIND_OFFICIAL_CONSENSUS_SOURCE",
    "manual_research_required": "MANUAL_RESEARCH_REQUIRED",
    "not_publicly_confirmable": "MARK_NOT_PUBLICLY_CONFIRMABLE",
}

TASK_INTENTS = {
    "ASP_price_proxy": "Find company commentary on 800G/1.6T product mix, ASP direction, price trend, or margin impact",
    "supplier_share": "Document whether supplier share can only be treated as a caveated range assumption",
    "customer_allocation_proxy": "Find public customer-side signal or caveated company commentary without confirming allocation",
    "official_consensus": "Find authorized official consensus source, or keep internal proxy separate",
    "shipment": "Find shipment, delivery, or order conversion commentary",
    "order_visibility": "Find order visibility, backlog, demand cadence, or customer order commentary",
    "industry_forecast": "Find public industry forecast for AI optical demand, 800G/1.6T shipment, or pricing context",
    "margin_signal": "Find margin or product mix commentary connected to high-speed optical products",
    "product_exposure": "Find product exposure disclosure for high-speed optical modules",
}

DO_NOT_DO = {
    "supplier_share": ["do not infer exact supplier share if not disclosed", "do not mark semantic evidence as confirmed share"],
    "ASP_price_proxy": ["do not infer exact ASP if not disclosed", "do not treat product mix as ASP unless explicitly stated"],
    "customer_allocation_proxy": ["do not infer named customer allocation", "do not treat order visibility as customer allocation"],
    "official_consensus": ["do not treat internal proxy as official consensus", "do not cite unauthorized consensus data"],
}
DEFAULT_DO_NOT_DO = ["do not create pending", "do not write evidence in this planning step", "do not remove source caveats"]


def _task_id(ticker: str, variable: str, route_type: str) -> str:
    digest = hashlib.sha1(f"{ticker}|{variable}|{route_type}".encode("utf-8")).hexdigest()[:8]
    return f"phase36_{ticker.replace('.', '_').lower()}_{variable.lower()}_{digest}"


def _allowed_usage_target(route: dict[str, Any]) -> str:
    usage = str(route.get("allowed_usage") or "")
    if "valuation_support" in usage:
        return "valuation_support"
    if usage in {"supporting_evidence", "scenario_analysis_only"}:
        return usage
    return "context_only"


def build_evidence_acquisition_tasks(conn: sqlite3.Connection, ticker: str) -> dict[str, Any]:
    routes_payload = build_evidence_source_routes(conn, ticker)
    tasks: list[dict[str, Any]] = []
    for variable_row in routes_payload.get("source_routes") or []:
        variable = str(variable_row.get("variable") or "")
        for route in variable_row.get("source_routes") or []:
            route_type = str(route.get("route_type") or "")
            task_type = ROUTE_TO_TASK_TYPE.get(route_type, "MANUAL_RESEARCH_REQUIRED")
            tasks.append(
                {
                    "task_id": _task_id(str(routes_payload.get("ticker")), variable, route_type),
                    "variable": variable,
                    "task_type": task_type,
                    "route_type": route_type,
                    "priority": route.get("priority") or "medium",
                    "query_intent": TASK_INTENTS.get(variable, f"Find evidence for {variable}"),
                    "expected_output": "quoted_span evidence candidate" if task_type not in {"MARK_NOT_PUBLICLY_CONFIRMABLE"} else "explicit not-publicly-confirmable note",
                    "allowed_usage_target": _allowed_usage_target(route),
                    "expected_evidence_type": route.get("expected_evidence_type"),
                    "limitations": route.get("limitations") or [],
                    "do_not_do": list(dict.fromkeys(DO_NOT_DO.get(variable, []) + DEFAULT_DO_NOT_DO)),
                    "new_pending_created": False,
                }
            )
    return {
        "generated_at": now_ts(),
        "ticker": routes_payload.get("ticker"),
        "company_name": routes_payload.get("company_name"),
        "evidence_acquisition_tasks": tasks,
        "summary": {
            "tasks": len(tasks),
            "high_priority_tasks": sum(1 for task in tasks if task.get("priority") == "high"),
            "manual_research_required": sum(1 for task in tasks if task.get("task_type") == "MANUAL_RESEARCH_REQUIRED"),
            "not_publicly_confirmable": sum(1 for task in tasks if task.get("task_type") == "MARK_NOT_PUBLICLY_CONFIRMABLE"),
            "new_pending_created": 0,
            "paper_order_created": 0,
        },
        "safety": {
            "task_planning_only": True,
            "fetch_executed": False,
            "evidence_written": False,
            "promotion_rules_relaxed": False,
        },
    }
