#!/usr/bin/env python3
"""Specific evidence request builder for Phase 40 research review."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker, review_candidate_id_for
from smr_wiki import now_ts


SUPPORTED_EVIDENCE_TYPES = {
    "supplier_share",
    "official_consensus",
    "confirmed_customer_allocation",
    "ASP_price_proxy",
    "customer_side_signal",
    "bear_case_evidence",
    "industry_forecast",
}

REQUEST_TEMPLATES: dict[str, dict[str, Any]] = {
    "supplier_share": {
        "priority": "high_but_low_public_availability",
        "reason": "Supplier share is needed before company-specific revenue sensitivity can move beyond scenarios.",
        "allowed_source_route": "scenario_analysis_only",
        "availability_judgment": "low_public_availability",
        "feasibility": "manual_research_required",
        "allowed_usage": "scenario_analysis_only",
        "expected_output": "source route and scenario-only supplier share assumption boundary",
        "do_not_do": [
            "do not fabricate exact share",
            "do not infer share from generic demand",
            "do not mark supplier share scenario as confirmed",
        ],
    },
    "official_consensus": {
        "priority": "high",
        "reason": "Official consensus is required to benchmark expectation gap reliably.",
        "allowed_source_route": "authorized_source_required",
        "availability_judgment": "commercial_source_required",
        "feasibility": "authorized_source_required",
        "allowed_usage": "expectation_gap_benchmark_if_authorized",
        "expected_output": "authorized consensus availability check without treating internal proxy as official consensus",
        "do_not_do": [
            "do not treat internal proxy as official consensus",
            "do not infer consensus from management commentary",
            "do not scrape restricted consensus data",
        ],
    },
    "confirmed_customer_allocation": {
        "priority": "high",
        "reason": "Customer allocation must be confirmed before investment promotion can rely on customer-specific exposure.",
        "allowed_source_route": "customer-side public signal or company direct disclosure",
        "availability_judgment": "proxy_only_until_direct_confirmation",
        "feasibility": "manual_research_required",
        "allowed_usage": "scenario_analysis_only",
        "expected_output": "customer allocation route check with proxy boundary preserved",
        "do_not_do": [
            "do not convert customer proxy into confirmed allocation",
            "do not name a customer without direct public support",
            "do not treat order visibility as confirmed customer allocation",
        ],
    },
    "ASP_price_proxy": {
        "priority": "medium",
        "reason": "ASP proxy evidence can support valuation context but cannot become confirmed ASP.",
        "allowed_source_route": "company disclosure or auditable pricing proxy",
        "availability_judgment": "proxy_possible",
        "feasibility": "medium",
        "allowed_usage": "valuation_support",
        "expected_output": "auditable ASP proxy route without confirming exact ASP",
        "do_not_do": [
            "do not treat product mix as exact ASP",
            "do not infer exact pricing from management tone",
        ],
    },
    "customer_side_signal": {
        "priority": "medium",
        "reason": "Customer-side public signals can help validate demand without confirming allocation.",
        "allowed_source_route": "public customer disclosure or verifiable ecosystem signal",
        "availability_judgment": "public_signal_possible",
        "feasibility": "medium",
        "allowed_usage": "supporting_evidence",
        "expected_output": "traceable customer-side signal, not confirmed allocation",
        "do_not_do": [
            "do not infer confirmed allocation from generic customer demand",
            "do not upgrade proxy evidence into named-customer confirmation",
        ],
    },
    "bear_case_evidence": {
        "priority": "medium",
        "reason": "Bear-case evidence is needed to test whether stronger product and shipment support actually reduces downside risk.",
        "allowed_source_route": "public disclosure or source-backed counterevidence",
        "availability_judgment": "available_with_manual_review",
        "feasibility": "medium",
        "allowed_usage": "bear_case_context",
        "expected_output": "bear-case support or counterevidence without promotion",
        "do_not_do": [
            "do not ignore contrary evidence",
            "do not mark a bear case mitigated without source-backed support",
        ],
    },
    "industry_forecast": {
        "priority": "medium_low",
        "reason": "Industry forecasts can add context but cannot replace company-specific evidence.",
        "allowed_source_route": "reputable public forecast or source-cited industry report",
        "availability_judgment": "available_as_context",
        "feasibility": "medium",
        "allowed_usage": "supporting_context_only",
        "expected_output": "industry context only, not company-specific order evidence",
        "do_not_do": [
            "do not treat industry forecast as company-specific order",
            "do not use unsourced forecast as official consensus",
        ],
    },
}


def dumps_json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, sort_keys=True, default=str)


def loads_json(raw: str | None, fallback: Any) -> Any:
    if raw in (None, ""):
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def ensure_specific_evidence_request_table(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS research_specific_evidence_requests (
            request_id TEXT PRIMARY KEY,
            ticker TEXT NOT NULL,
            review_candidate_id TEXT NOT NULL,
            evidence_type TEXT NOT NULL,
            priority TEXT NOT NULL,
            reason TEXT NOT NULL,
            allowed_source_route TEXT NOT NULL,
            do_not_do_json TEXT NOT NULL DEFAULT '[]',
            status TEXT NOT NULL DEFAULT 'open',
            source_action TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            metadata_json TEXT NOT NULL DEFAULT '{}'
        );

        CREATE INDEX IF NOT EXISTS idx_research_specific_evidence_ticker
        ON research_specific_evidence_requests(ticker, status, updated_at DESC);

        CREATE UNIQUE INDEX IF NOT EXISTS idx_research_specific_evidence_dedupe
        ON research_specific_evidence_requests(ticker, evidence_type);
        """
    )


def evidence_request_id_for(ticker: str, evidence_type: str) -> str:
    code = normalize_ticker(ticker).split(".")[0].lower()
    return f"specific_evidence_{code}_{evidence_type}"


def build_specific_evidence_request(
    ticker: str = TARGET_REVIEW_TICKER,
    evidence_type: str = "official_consensus",
    *,
    review_candidate_id: str | None = None,
    source_action: str | None = None,
) -> dict[str, Any]:
    ticker = normalize_ticker(ticker)
    if evidence_type not in SUPPORTED_EVIDENCE_TYPES:
        raise ValueError(f"Unsupported specific evidence type: {evidence_type}")
    template = REQUEST_TEMPLATES[evidence_type]
    timestamp = now_ts()
    return {
        "request_id": evidence_request_id_for(ticker, evidence_type),
        "ticker": ticker,
        "review_candidate_id": review_candidate_id or review_candidate_id_for(ticker),
        "evidence_type": evidence_type,
        "priority": template["priority"],
        "reason": template["reason"],
        "allowed_source_route": template["allowed_source_route"],
        "availability_judgment": template["availability_judgment"],
        "feasibility": template["feasibility"],
        "allowed_usage": template["allowed_usage"],
        "expected_output": template["expected_output"],
        "do_not_do": list(template["do_not_do"]),
        "status": "open",
        "source_action": source_action,
        "created_at": timestamp,
        "updated_at": timestamp,
        "metadata": {
            "request_builder_only": True,
            "availability_judgment": template["availability_judgment"],
            "feasibility": template["feasibility"],
            "allowed_usage": template["allowed_usage"],
            "expected_output": template["expected_output"],
            "evidence_written": False,
            "pending_created": False,
            "promotion_allowed": False,
        },
    }


def _row_to_dict(row: sqlite3.Row | tuple[Any, ...] | None) -> dict[str, Any]:
    if not row:
        return {}
    keys = [
        "request_id",
        "ticker",
        "review_candidate_id",
        "evidence_type",
        "priority",
        "reason",
        "allowed_source_route",
        "do_not_do_json",
        "status",
        "source_action",
        "created_at",
        "updated_at",
        "metadata_json",
    ]
    data = dict(zip(keys, row))
    data["do_not_do"] = loads_json(data.pop("do_not_do_json"), [])
    data["metadata"] = loads_json(data.pop("metadata_json"), {})
    metadata = data.get("metadata") or {}
    for key in ("availability_judgment", "feasibility", "allowed_usage", "expected_output"):
        if key in metadata:
            data[key] = metadata[key]
    return data


def upsert_specific_evidence_request(
    conn: sqlite3.Connection,
    *,
    ticker: str = TARGET_REVIEW_TICKER,
    evidence_type: str = "official_consensus",
    review_candidate_id: str | None = None,
    source_action: str | None = None,
) -> dict[str, Any]:
    ensure_specific_evidence_request_table(conn)
    request = build_specific_evidence_request(
        ticker,
        evidence_type,
        review_candidate_id=review_candidate_id,
        source_action=source_action,
    )
    existing = get_specific_evidence_request(conn, request["request_id"])
    created_at = existing.get("created_at") or request["created_at"]
    conn.execute(
        """
        INSERT INTO research_specific_evidence_requests (
            request_id, ticker, review_candidate_id, evidence_type, priority,
            reason, allowed_source_route, do_not_do_json, status, source_action,
            created_at, updated_at, metadata_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(request_id) DO UPDATE SET
            priority=excluded.priority,
            reason=excluded.reason,
            allowed_source_route=excluded.allowed_source_route,
            do_not_do_json=excluded.do_not_do_json,
            status=excluded.status,
            source_action=excluded.source_action,
            updated_at=excluded.updated_at,
            metadata_json=excluded.metadata_json
        """,
        (
            request["request_id"],
            request["ticker"],
            request["review_candidate_id"],
            request["evidence_type"],
            request["priority"],
            request["reason"],
            request["allowed_source_route"],
            dumps_json(request["do_not_do"]),
            request["status"],
            request.get("source_action"),
            created_at,
            now_ts(),
            dumps_json(request["metadata"]),
        ),
    )
    return get_specific_evidence_request(conn, request["request_id"])


def get_specific_evidence_request(conn: sqlite3.Connection, request_id: str) -> dict[str, Any]:
    ensure_specific_evidence_request_table(conn)
    row = conn.execute(
        """
        SELECT request_id, ticker, review_candidate_id, evidence_type, priority,
               reason, allowed_source_route, do_not_do_json, status, source_action,
               created_at, updated_at, metadata_json
        FROM research_specific_evidence_requests
        WHERE request_id=?
        LIMIT 1
        """,
        (request_id,),
    ).fetchone()
    return _row_to_dict(row)


def list_specific_evidence_requests(
    conn: sqlite3.Connection,
    *,
    ticker: str | None = None,
    status: str | None = None,
) -> list[dict[str, Any]]:
    ensure_specific_evidence_request_table(conn)
    filters = []
    params: list[Any] = []
    if ticker:
        filters.append("ticker=?")
        params.append(normalize_ticker(ticker))
    if status:
        filters.append("status=?")
        params.append(status)
    where = "WHERE " + " AND ".join(filters) if filters else ""
    rows = conn.execute(
        f"""
        SELECT request_id, ticker, review_candidate_id, evidence_type, priority,
               reason, allowed_source_route, do_not_do_json, status, source_action,
               created_at, updated_at, metadata_json
        FROM research_specific_evidence_requests
        {where}
        ORDER BY
            CASE priority
                WHEN 'high' THEN 0
                WHEN 'high_but_low_public_availability' THEN 1
                WHEN 'medium' THEN 2
                ELSE 3
            END,
            evidence_type
        """,
        params,
    ).fetchall()
    return [_row_to_dict(row) for row in rows]
