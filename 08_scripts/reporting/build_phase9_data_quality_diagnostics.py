#!/usr/bin/env python3
"""Phase 9 field/evidence-level data-quality diagnostics."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

LIB_DIR = Path(__file__).resolve().parents[1] / "lib"
if str(LIB_DIR) not in sys.path:
    sys.path.insert(0, str(LIB_DIR))

from smr_agents import DB_PATH
from smr_blocker_taxonomy import normalize_blocker
from smr_data_quality_gate import build_data_quality_gate
from smr_evidence_quality import ensure_evidence_quality_columns, update_evidence_quality_scores
from smr_fundamentals import FUNDAMENTAL_FIELDS, build_fundamentals_snapshot, latest_fundamentals_snapshot
from smr_phase6_watchlists import load_watchlist_config
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts


SCRIPT_NAME = "build_phase9_data_quality_diagnostics.py"

MISSING_REASON_TO_CODE = {
    "mapping_missing": "FIELD_MAPPING_MISSING",
    "field_not_found": "FIELD_NOT_FOUND",
    "table_not_found": "TABLE_NOT_FOUND",
    "parse_failed": "PARSE_FAILED",
    "ambiguous_unit": "AMBIGUOUS_UNIT",
    "stale_filing": "STALE_SOURCE_EVIDENCE",
    "derived_field_missing_inputs": "FIELD_NOT_FOUND",
    "needs_manual_review": "TABLE_EXTRACTION_CONFIDENCE_LOW",
}


def market_for_ticker(ticker: str | None) -> str:
    text = str(ticker or "").upper()
    if text.endswith((".SZ", ".SH", ".BJ")):
        return "A"
    if text.endswith(".HK"):
        return "HK"
    return "US"


def field_quality_from_snapshot(snapshot: dict[str, Any]) -> dict[str, Any]:
    details = snapshot.get("field_details") or {}
    missing_reasons = snapshot.get("field_missing_reasons") or {}
    result: dict[str, Any] = {}
    for field in FUNDAMENTAL_FIELDS:
        detail = dict(details.get(field) or {})
        value = detail.get("extracted_value")
        if value is None and snapshot.get(field) is not None:
            value = snapshot.get(field)
        missing_reason = detail.get("missing_reason") or missing_reasons.get(field)
        status = "extracted" if value is not None and not missing_reason else "missing"
        result[field] = {
            "status": status,
            "extracted_value": value,
            "confidence": float(detail.get("confidence") or 0.0),
            "confidence_breakdown": detail.get("confidence_breakdown") or {},
            "confidence_level": detail.get("confidence_level"),
            "allowed_usage": detail.get("allowed_usage"),
            "missing_reason": None if status == "extracted" else (missing_reason or "field_not_found"),
            "unit": detail.get("unit"),
            "currency": detail.get("currency"),
            "unit_confidence": detail.get("unit_confidence"),
            "unit_warning": detail.get("unit_warning"),
            "period": detail.get("period") or snapshot.get("period"),
            "source_evidence_id": detail.get("source_evidence_id"),
            "source_evidence_ids": detail.get("source_evidence_ids") or [],
            "source_filing_id": detail.get("source_filing_id"),
            "source_chunk_id": detail.get("source_chunk_id") or detail.get("chunk_id"),
            "source_section_type": detail.get("source_section_type") or detail.get("chunk_section_type"),
            "source_url": detail.get("source_url"),
            "published_at": detail.get("published_at"),
            "warnings": detail.get("warnings") or [],
        }
    return result


def root_causes_from_field_quality(field_quality: dict[str, Any]) -> list[dict[str, Any]]:
    causes: list[dict[str, Any]] = []
    for field, detail in field_quality.items():
        if detail.get("status") == "missing":
            reason = detail.get("missing_reason") or "field_not_found"
            code = MISSING_REASON_TO_CODE.get(reason, "FIELD_NOT_FOUND")
            causes.append(
                normalize_blocker(
                    {
                        "code": code,
                        "message": f"{field} missing: {reason}",
                        "affected_fields": [field],
                        "suggested_fix": suggested_field_fix(field, reason),
                    }
                )
            )
        elif detail.get("allowed_usage") == "blocked" and (
            detail.get("unit_warning") in {"ambiguous_unit", "percentage_not_amount"}
            or "ambiguous_unit" in set(detail.get("warnings") or [])
        ):
            causes.append(
                normalize_blocker(
                    {
                        "code": "AMBIGUOUS_UNIT",
                        "message": f"{field} has blocked or ambiguous unit",
                        "affected_fields": [field],
                        "suggested_fix": suggested_field_fix(field, "ambiguous_unit"),
                    }
                )
            )
        elif float(detail.get("confidence") or 0.0) < 0.5 or detail.get("confidence_level") in {"low", "blocked"}:
            causes.append(
                normalize_blocker(
                    {
                        "code": "FUNDAMENTALS_FIELD_CONFIDENCE_LOW",
                        "message": f"{field} confidence below threshold",
                        "affected_fields": [field],
                        "suggested_fix": f"improve extraction confidence for {field} or mark needs_manual_review",
                    }
                )
            )
        if detail.get("status") == "extracted" and not detail.get("source_evidence_id"):
            causes.append(
                normalize_blocker(
                    {
                        "code": "MISSING_SOURCE_EVIDENCE_ID",
                        "message": f"{field} has no source_evidence_id",
                        "affected_fields": [field],
                    }
                )
            )
    return causes


def data_quality_status(root_causes: list[dict[str, Any]], evidence_issues: list[dict[str, Any]] | None = None) -> str:
    evidence_issues = evidence_issues or []
    if root_causes or any(issue.get("issue_code") in {"EVIDENCE_QUALITY_LOW", "FILING_CHUNK_RELEVANCE_LOW"} for issue in evidence_issues):
        return "degraded"
    if any(cause.get("severity") == "high" for cause in root_causes):
        return "degraded"
    return "pass"


def root_cause_keys(root_causes: list[dict[str, Any]]) -> list[str]:
    keys = []
    for cause in root_causes:
        fields = cause.get("affected_fields") or []
        if fields:
            keys.extend(f"{cause.get('code')}:{field}" for field in fields)
        else:
            keys.append(str(cause.get("code") or "UNKNOWN"))
    return sorted(set(keys))


def field_changes(before_fields: dict[str, Any], after_fields: dict[str, Any]) -> dict[str, Any]:
    changes: dict[str, Any] = {}
    for field in sorted(set(before_fields) | set(after_fields)):
        before = before_fields.get(field) or {}
        after = after_fields.get(field) or {}
        before_status = before.get("status")
        after_status = after.get("status")
        before_reason = before.get("missing_reason")
        after_reason = after.get("missing_reason")
        if before_status != after_status or before_reason != after_reason:
            changes[field] = {
                "before": before_status,
                "after": after_status,
                "before_missing_reason": before_reason,
                "missing_reason": after_reason,
                "before_allowed_usage": before.get("allowed_usage"),
                "after_allowed_usage": after.get("allowed_usage"),
                "before_confidence": before.get("confidence"),
                "after_confidence": after.get("confidence"),
            }
        elif before.get("allowed_usage") != after.get("allowed_usage") or before.get("confidence") != after.get("confidence"):
            changes[field] = {
                "before": before_status,
                "after": after_status,
                "before_missing_reason": before_reason,
                "missing_reason": after_reason,
                "before_allowed_usage": before.get("allowed_usage"),
                "after_allowed_usage": after.get("allowed_usage"),
                "before_confidence": before.get("confidence"),
                "after_confidence": after.get("confidence"),
            }
    return changes


def suggested_field_fix(field: str, reason: str) -> str:
    if reason == "mapping_missing":
        return f"add HK/CN synonyms for {field}"
    if reason == "table_not_found":
        return f"improve financial table detection for {field}"
    if reason == "parse_failed":
        return f"fix parser handling for matched {field} table text"
    if reason == "ambiguous_unit":
        return f"resolve unit/currency ambiguity for {field}"
    if reason == "derived_field_missing_inputs":
        return f"extract input fields required to derive {field}"
    return f"inspect source filing and add extraction coverage for {field}"


def evidence_issues(conn: sqlite3.Connection, ticker: str, limit: int = 20) -> list[dict[str, Any]]:
    ensure_evidence_quality_columns(conn)
    update_evidence_quality_scores(conn, ticker=ticker, limit=500)
    rows = conn.execute(
        """
        SELECT evidence_id, source_key, source_type, source_quality, source_status,
               quality_score, directness, ticker_relevance, theme_relevance,
               investment_relevance_score, section_type_score,
               usable_for_core_claim, usable_for_promotion, quality_metadata_json
        FROM evidence_items
        WHERE metadata_json LIKE ? OR text_excerpt LIKE ?
        ORDER BY COALESCE(quality_score, 0) ASC, id DESC
        LIMIT ?
        """,
        (f"%{ticker}%", f"%{ticker}%", max(1, int(limit))),
    ).fetchall()
    issues: list[dict[str, Any]] = []
    for row in rows:
        metadata = json.loads(row[13] or "{}")
        issue_code = None
        if row[5] is not None and float(row[5]) < 0.55:
            issue_code = "EVIDENCE_QUALITY_LOW"
        if metadata.get("chunk_section_type") in {"administrative", "cover_page", "signature", "exhibit_index", "legal_boilerplate"}:
            issue_code = "FILING_CHUNK_RELEVANCE_LOW"
        if row[6] == "low":
            issue_code = "LOW_DIRECTNESS_EVIDENCE"
        if row[7] is not None and float(row[7]) < 0.5:
            issue_code = "LOW_TICKER_RELEVANCE"
        if issue_code:
            issues.append(
                {
                    "evidence_id": row[0],
                    "source_key": row[1],
                    "source_type": row[2],
                    "issue_code": issue_code,
                    "quality_score": row[5],
                    "directness": row[6],
                    "ticker_relevance": row[7],
                    "theme_relevance": row[8],
                    "investment_relevance_score": row[9],
                    "section_type_score": row[10],
                    "section_type": metadata.get("chunk_section_type"),
                    "usable_for_core_claim": bool(row[11]) if row[11] is not None else None,
                    "usable_for_promotion": bool(row[12]) if row[12] is not None else None,
                }
            )
    return issues


def build_diagnostics(
    conn: sqlite3.Connection,
    ticker: str,
    *,
    refresh_fundamentals: bool = False,
    limit: int = 20,
    thesis_types: list[str] | None = None,
) -> dict[str, Any]:
    before_snapshot = latest_fundamentals_snapshot(conn, ticker)
    if refresh_fundamentals:
        snapshot = build_fundamentals_snapshot(conn, ticker, prefer_live=True)
    else:
        snapshot = before_snapshot or build_fundamentals_snapshot(conn, ticker, prefer_live=True)
    fields = field_quality_from_snapshot(snapshot)
    root_causes = root_causes_from_field_quality(fields)
    issues = evidence_issues(conn, ticker, limit=limit)
    status = data_quality_status(root_causes, issues)
    payload = {
        "generated_at": now_ts(),
        "ticker": ticker.upper(),
        "market": market_for_ticker(ticker),
        "overall_data_quality_status": status,
        "fundamentals_snapshot_id": snapshot.get("snapshot_id"),
        "fundamentals_status": snapshot.get("freshness_status"),
        "root_causes": root_causes,
        "evidence_issues": issues,
        "field_quality": fields,
    }
    if thesis_types:
        payload["data_quality_gate"] = build_data_quality_gate(
            ticker=ticker,
            thesis_types=thesis_types,
            root_causes=root_causes,
            field_quality=fields,
            before_status=status,
        )
    if refresh_fundamentals and before_snapshot:
        before_fields = field_quality_from_snapshot(before_snapshot)
        before_causes = root_causes_from_field_quality(before_fields)
        before_keys = root_cause_keys(before_causes)
        after_keys = root_cause_keys(root_causes)
        payload["before"] = {
            "status": data_quality_status(before_causes),
            "root_causes": before_keys,
        }
        payload["after"] = {
            "status": status,
            "root_causes": after_keys,
            "resolved_root_causes": sorted(set(before_keys) - set(after_keys)),
        }
        payload["field_changes"] = field_changes(before_fields, fields)
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 9 Data Quality Diagnostics",
        "",
        f"- ticker: `{payload.get('ticker')}`",
        f"- status: `{payload.get('overall_data_quality_status')}`",
        f"- fundamentals_status: `{payload.get('fundamentals_status')}`",
        "",
        "## Root Causes",
        "",
        "| Code | Field | Severity | Suggested Fix |",
        "|---|---|---|---|",
    ]
    for cause in payload.get("root_causes") or []:
        lines.append(
            f"| {cause.get('code')} | {', '.join(cause.get('affected_fields') or []) or '-'} | {cause.get('severity')} | {cause.get('suggested_fix')} |"
        )
    lines.extend(["", "## Field Quality", "", "| Field | Status | Confidence | Missing Reason | Evidence |", "|---|---|---:|---|---|"])
    for field, detail in payload.get("field_quality", {}).items():
        lines.append(
            f"| {field} | {detail.get('status')} | {detail.get('confidence')} | {detail.get('missing_reason') or '-'} | {detail.get('source_evidence_id') or '-'} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 9 data quality diagnostics")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker")
    parser.add_argument("--watchlist")
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    parser.add_argument("--refresh-fundamentals", action="store_true")
    parser.add_argument("--thesis", action="append", default=None)
    args = parser.parse_args()

    conn = sqlite3.connect(args.db_path)
    conn.row_factory = sqlite3.Row
    try:
        if args.watchlist:
            config = load_watchlist_config(args.watchlist)
            payload = {
                "generated_at": now_ts(),
                "watchlist_id": args.watchlist,
                "results": [
                    build_diagnostics(
                        conn,
                        item["ticker"],
                        refresh_fundamentals=args.refresh_fundamentals,
                        limit=args.limit,
                        thesis_types=args.thesis,
                    )
                    for item in (config.get("tickers") or [])[: args.limit]
                ],
            }
        else:
            payload = build_diagnostics(
                conn,
                args.ticker or "09988.HK",
                refresh_fundamentals=args.refresh_fundamentals,
                limit=args.limit,
                thesis_types=args.thesis,
            )
        register_snapshot(
            conn,
            entity_type="phase9_data_quality_diagnostics",
            entity_id=(args.watchlist or args.ticker or "09988.HK").upper(),
            status=payload.get("overall_data_quality_status") or "ok",
            source=SCRIPT_NAME,
            payload=payload,
        )
        conn.commit()
    finally:
        conn.close()
    if args.markdown and not args.json and not args.watchlist:
        print(render_markdown(payload))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase9 data quality diagnostics built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
