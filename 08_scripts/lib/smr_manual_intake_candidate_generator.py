#!/usr/bin/env python3
"""Generate Phase 43 manual evidence candidates from manual source intake."""

from __future__ import annotations

import json
import sqlite3
from typing import Any

from smr_manual_intake_payload import list_manual_intake_payloads
from smr_manual_intake_rejection import build_rejection_record, dumps_json, loads_json, write_rejection_records
from smr_manual_source_intake_validator import validate_manual_source_intake
from smr_research_review_lifecycle import TARGET_REVIEW_TICKER, normalize_ticker
from smr_wiki import now_ts


AUTHORIZED_CONSENSUS_TYPES = {"authorized_consensus_source", "sell_side_authorized_note"}
UNAUTHORIZED_PERMISSIONS = {"unauthorized", "internal_only", "restricted_without_permission"}

FINAL_ALLOWED_USAGE = {
    "official_consensus": "expectation_gap_benchmark_if_authorized",
    "supplier_share": "scenario_analysis_only",
    "confirmed_customer_allocation": "bear_case_context_or_scenario_support",
}

CONFIRMATION_STATUS = {
    "official_consensus": "candidate_not_confirmed",
    "supplier_share": "scenario_not_confirmed",
    "confirmed_customer_allocation": "proxy_not_confirmed",
}

VARIABLE_TYPE = {
    "official_consensus": "official_consensus_candidate",
    "supplier_share": "supplier_share_scenario",
    "confirmed_customer_allocation": "customer_allocation_proxy",
}


def _has_text(value: Any) -> bool:
    return bool(str(value or "").strip())


def _validation_payload(payload: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(payload)
    normalized["allowed_usage_requested"] = payload.get("requested_allowed_usage") or payload.get("allowed_usage_requested")
    return normalized


def _requested_confirmed_usage(value: Any) -> bool:
    text = str(value or "").strip().lower()
    return text in {
        "confirmed",
        "confirmed_evidence",
        "confirmed_supplier_share",
        "confirmed_customer_allocation",
        "research_evidence_if_directly_disclosed",
    }


def validate_phase43_manual_payload(payload: dict[str, Any]) -> dict[str, Any]:
    phase42 = validate_manual_source_intake(_validation_payload(payload)).get("validation_result") or {}
    evidence_type = str(payload.get("evidence_type") or "")
    source_type = str(payload.get("source_type") or "")
    permission = str(payload.get("permission_status") or "")
    requested = payload.get("requested_allowed_usage") or payload.get("allowed_usage_requested")
    blocked = list(phase42.get("blocked_reasons") or [])
    reasons = list(phase42.get("reasons") or [])

    if not _has_text(payload.get("quoted_span")):
        blocked.append("quoted_span_required")
    if not _has_text(payload.get("source_url_or_reference")):
        blocked.append("source_url_or_reference_required")
    if permission in UNAUTHORIZED_PERMISSIONS:
        blocked.append("permission_status_unauthorized")

    if evidence_type == "official_consensus":
        if source_type not in AUTHORIZED_CONSENSUS_TYPES:
            blocked.append("internal_proxy_cannot_be_official_consensus")
        if permission != "authorized_or_user_provided":
            blocked.append("authorized_permission_required")
        if not _has_text(payload.get("source_provider")):
            blocked.append("source_provider_required")
        if not _has_text(payload.get("source_date")):
            blocked.append("source_date_required")
    elif evidence_type == "supplier_share":
        if source_type == "scenario_assumption" and _requested_confirmed_usage(requested):
            blocked.append("supplier_share_scenario_cannot_request_confirmed")
    elif evidence_type == "confirmed_customer_allocation":
        if source_type == "proxy_evidence_note" and _requested_confirmed_usage(requested):
            blocked.append("customer_allocation_proxy_cannot_request_confirmed")

    blocked = list(dict.fromkeys(blocked))
    input_valid = not blocked and bool(phase42.get("can_create_evidence_candidate"))
    if input_valid:
        reasons.append("phase43 permission and source metadata guard passed")
    return {
        "evidence_type": evidence_type,
        "source_type": source_type,
        "input_valid": input_valid,
        "can_create_evidence_candidate": bool(input_valid),
        "can_be_confirmed": False,
        "allowed_usage": FINAL_ALLOWED_USAGE.get(evidence_type, phase42.get("allowed_usage") or "blocked") if input_valid else "blocked",
        "reasons": list(dict.fromkeys(reasons)),
        "blocked_reasons": blocked,
        "phase42_validation": phase42,
        "pending_created": 0,
        "paper_order_created": 0,
        "promotion_allowed": False,
    }


def candidate_id_for_intake(intake_id: str) -> str:
    value = str(intake_id or "manual_intake_unknown")
    if value.startswith("manual_intake_"):
        return value.replace("manual_intake_", "manual_candidate_", 1)
    return f"manual_candidate_{value}"


def candidate_from_payload(payload: dict[str, Any], validation: dict[str, Any]) -> dict[str, Any]:
    evidence_type = str(payload.get("evidence_type") or "")
    limitations = list(payload.get("limitations") or [])
    if "candidate is not confirmed evidence" not in limitations:
        limitations.append("candidate is not confirmed evidence")
    return {
        "candidate_id": candidate_id_for_intake(str(payload.get("intake_id") or "")),
        "intake_id": payload.get("intake_id"),
        "ticker": normalize_ticker(str(payload.get("ticker") or TARGET_REVIEW_TICKER)),
        "evidence_type": evidence_type,
        "source_type": payload.get("source_type"),
        "source_title": payload.get("source_title"),
        "source_provider": payload.get("source_provider"),
        "source_date": payload.get("source_date"),
        "source_url_or_reference": payload.get("source_url_or_reference"),
        "permission_status": payload.get("permission_status"),
        "quoted_span": payload.get("quoted_span"),
        "requested_allowed_usage": payload.get("requested_allowed_usage") or payload.get("allowed_usage_requested"),
        "allowed_usage": validation.get("allowed_usage") or FINAL_ALLOWED_USAGE.get(evidence_type),
        "confirmation_status": CONFIRMATION_STATUS.get(evidence_type, "candidate_not_confirmed"),
        "variable_type": VARIABLE_TYPE.get(evidence_type, evidence_type),
        "limitations": limitations,
        "usable_for_promotion": False,
        "is_confirmed": False,
        "persisted": False,
        "created_at": now_ts(),
        "updated_at": now_ts(),
        "payload": {
            "manual_payload": payload,
            "validation_result": validation,
            "candidate_not_confirmed": True,
            "scenario_not_fact": evidence_type == "supplier_share",
            "proxy_not_confirmed_allocation": evidence_type == "confirmed_customer_allocation",
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_allowed": False,
        },
    }


def ensure_manual_intake_candidate_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS manual_intake_candidates (
            candidate_id TEXT PRIMARY KEY,
            intake_id TEXT NOT NULL,
            ticker TEXT NOT NULL,
            evidence_type TEXT NOT NULL,
            source_type TEXT NOT NULL,
            source_title TEXT,
            source_provider TEXT,
            source_date TEXT,
            source_url_or_reference TEXT NOT NULL,
            permission_status TEXT NOT NULL,
            quoted_span TEXT NOT NULL,
            requested_allowed_usage TEXT,
            allowed_usage TEXT NOT NULL,
            confirmation_status TEXT NOT NULL,
            variable_type TEXT,
            limitations_json TEXT NOT NULL DEFAULT '[]',
            payload_json TEXT NOT NULL DEFAULT '{}',
            usable_for_promotion INTEGER NOT NULL DEFAULT 0,
            is_confirmed INTEGER NOT NULL DEFAULT 0,
            persisted INTEGER NOT NULL DEFAULT 0,
            pending_created INTEGER NOT NULL DEFAULT 0,
            paper_order_created INTEGER NOT NULL DEFAULT 0,
            promotion_allowed INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
        """
    )
    conn.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_manual_intake_candidates_intake
        ON manual_intake_candidates(intake_id)
        """
    )


def _row_to_candidate(row: sqlite3.Row | tuple[Any, ...]) -> dict[str, Any]:
    return {
        "candidate_id": row[0],
        "intake_id": row[1],
        "ticker": row[2],
        "evidence_type": row[3],
        "source_type": row[4],
        "source_title": row[5],
        "source_provider": row[6],
        "source_date": row[7],
        "source_url_or_reference": row[8],
        "permission_status": row[9],
        "quoted_span": row[10],
        "requested_allowed_usage": row[11],
        "allowed_usage": row[12],
        "confirmation_status": row[13],
        "variable_type": row[14],
        "limitations": loads_json(row[15], []),
        "payload": loads_json(row[16], {}),
        "usable_for_promotion": bool(row[17]),
        "is_confirmed": bool(row[18]),
        "persisted": bool(row[19]),
        "pending_created": bool(row[20]),
        "paper_order_created": bool(row[21]),
        "promotion_allowed": bool(row[22]),
        "created_at": row[23],
        "updated_at": row[24],
    }


def list_manual_intake_candidates(
    conn: sqlite3.Connection,
    *,
    ticker: str | None = None,
    persisted: bool | None = None,
) -> list[dict[str, Any]]:
    ensure_manual_intake_candidate_table(conn)
    filters = []
    params: list[Any] = []
    if ticker:
        filters.append("ticker=?")
        params.append(normalize_ticker(ticker))
    if persisted is not None:
        filters.append("persisted=?")
        params.append(1 if persisted else 0)
    where = "WHERE " + " AND ".join(filters) if filters else ""
    rows = conn.execute(
        f"""
        SELECT candidate_id, intake_id, ticker, evidence_type, source_type, source_title,
               source_provider, source_date, source_url_or_reference, permission_status,
               quoted_span, requested_allowed_usage, allowed_usage, confirmation_status,
               variable_type, limitations_json, payload_json, usable_for_promotion,
               is_confirmed, persisted, pending_created, paper_order_created,
               promotion_allowed, created_at, updated_at
        FROM manual_intake_candidates
        {where}
        ORDER BY ticker, evidence_type, candidate_id
        """,
        params,
    ).fetchall()
    return [_row_to_candidate(row) for row in rows]


def write_manual_intake_candidates(
    conn: sqlite3.Connection,
    candidates: list[dict[str, Any]],
    *,
    mark_persisted: bool = False,
) -> dict[str, int]:
    ensure_manual_intake_candidate_table(conn)
    written = 0
    duplicates = 0
    now = now_ts()
    for candidate in candidates:
        existing = conn.execute(
            "SELECT persisted FROM manual_intake_candidates WHERE candidate_id=? LIMIT 1",
            (candidate.get("candidate_id"),),
        ).fetchone()
        if existing:
            if mark_persisted and not bool(existing[0]):
                conn.execute(
                    """
                    UPDATE manual_intake_candidates
                    SET persisted=1, updated_at=?
                    WHERE candidate_id=?
                    """,
                    (now, candidate.get("candidate_id")),
                )
                written += 1
            else:
                duplicates += 1
            continue
        conn.execute(
            """
            INSERT INTO manual_intake_candidates (
                candidate_id, intake_id, ticker, evidence_type, source_type, source_title,
                source_provider, source_date, source_url_or_reference, permission_status,
                quoted_span, requested_allowed_usage, allowed_usage, confirmation_status,
                variable_type, limitations_json, payload_json, usable_for_promotion,
                is_confirmed, persisted, pending_created, paper_order_created,
                promotion_allowed, created_at, updated_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                candidate.get("candidate_id"),
                candidate.get("intake_id"),
                candidate.get("ticker"),
                candidate.get("evidence_type"),
                candidate.get("source_type"),
                candidate.get("source_title"),
                candidate.get("source_provider"),
                candidate.get("source_date"),
                candidate.get("source_url_or_reference"),
                candidate.get("permission_status"),
                candidate.get("quoted_span"),
                candidate.get("requested_allowed_usage"),
                candidate.get("allowed_usage"),
                candidate.get("confirmation_status"),
                candidate.get("variable_type"),
                dumps_json(candidate.get("limitations") or []),
                dumps_json(candidate.get("payload") or {}),
                0,
                0,
                1 if mark_persisted else int(bool(candidate.get("persisted"))),
                0,
                0,
                0,
                candidate.get("created_at") or now,
                now,
            ),
        )
        written += 1
    return {"written": written, "duplicates_skipped": duplicates}


def build_candidate_generation_payload(
    conn: sqlite3.Connection | None = None,
    *,
    ticker: str = TARGET_REVIEW_TICKER,
    sample: str | None = None,
    mode: str = "dry_run",
) -> dict[str, Any]:
    if mode not in {"dry_run", "execute"}:
        raise ValueError(f"Unsupported mode: {mode}")
    ticker = normalize_ticker(ticker)
    payloads = list_manual_intake_payloads(ticker, sample=sample)
    candidate_rows: list[dict[str, Any]] = []
    rejection_rows: list[dict[str, Any]] = []
    validation_rows: list[dict[str, Any]] = []
    for payload in payloads:
        validation = validate_phase43_manual_payload(payload)
        validation_rows.append({"intake_id": payload.get("intake_id"), "validation_result": validation})
        if validation.get("input_valid") and validation.get("can_create_evidence_candidate"):
            candidate_rows.append(candidate_from_payload(payload, validation))
        else:
            rejection_rows.append(build_rejection_record(payload, validation.get("blocked_reasons") or ["invalid_manual_payload"]))

    candidates_written = 0
    candidate_duplicates = 0
    rejections_written = 0
    rejection_duplicates = 0
    if mode == "execute":
        if conn is None:
            raise ValueError("execute mode requires a sqlite connection")
        candidate_write = write_manual_intake_candidates(conn, candidate_rows)
        rejection_write = write_rejection_records(conn, rejection_rows)
        candidates_written = candidate_write["written"]
        candidate_duplicates = candidate_write["duplicates_skipped"]
        rejections_written = rejection_write["written"]
        rejection_duplicates = rejection_write["duplicates_skipped"]

    return {
        "generated_at": now_ts(),
        "ticker": ticker,
        "manual_intake_candidate_generation": {
            "mode": mode,
            "payloads_checked": len(payloads),
            "valid_payloads": len(candidate_rows),
            "candidates_created": len(candidate_rows),
            "rejection_records_created": len(rejection_rows),
            "dry_run_wrote_db": False if mode == "dry_run" else None,
            "candidates_written": candidates_written,
            "rejection_records_written": rejections_written,
            "duplicates_skipped": candidate_duplicates + rejection_duplicates,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_allowed_true": 0,
            "candidate_rows": candidate_rows,
            "rejection_rows": rejection_rows,
            "validation_rows": validation_rows,
        },
        "safety": {
            "candidate_is_confirmed_evidence": False,
            "scenario_is_fact": False,
            "proxy_is_confirmed_allocation": False,
            "pending_created": 0,
            "paper_order_created": 0,
            "promotion_rules_relaxed": False,
            "real_trade_risk": False,
        },
    }
