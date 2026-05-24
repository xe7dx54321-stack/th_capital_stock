#!/usr/bin/env python3
"""Phase 12 data-quality before/after report for A/H evidence hardening."""

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

from build_phase9_data_quality_diagnostics import (
    data_quality_status,
    field_changes,
    field_quality_from_snapshot,
    root_cause_keys,
    root_causes_from_field_quality,
)
from smr_agents import DB_PATH
from smr_fundamentals import FUNDAMENTAL_FIELDS, build_fundamentals_snapshot, latest_fundamentals_snapshot
from smr_registry import register_snapshot
from smr_runlog import log_run
from smr_wiki import now_ts


SCRIPT_NAME = "build_phase12_data_quality_before_after.py"


def loads_json(raw: str | None, fallback: Any) -> Any:
    if raw in (None, ""):
        return fallback
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return fallback


def _decode_row(row: sqlite3.Row) -> dict[str, Any]:
    data = {
        "snapshot_id": row["snapshot_id"],
        "ticker": row["ticker"],
        "market": row["market"],
        "period": row["period"],
        "fiscal_year": row["fiscal_year"],
        "fiscal_quarter": row["fiscal_quarter"],
        "source_evidence_ids": loads_json(row["source_evidence_ids_json"], []),
        "source_quality": row["source_quality"],
        "freshness_status": row["freshness_status"],
        "confidence": row["confidence"],
        "missing_fields": loads_json(row["missing_fields_json"], []),
        "field_details": loads_json(row["field_details_json"], {}),
        "field_missing_reasons": loads_json(row["field_missing_reasons_json"], {}),
        "created_at": row["created_at"],
        "metadata": loads_json(row["metadata_json"], {}),
    }
    for field in FUNDAMENTAL_FIELDS:
        data[field] = row[field]
    return data


def fundamentals_history(conn: sqlite3.Connection, ticker: str, limit: int = 30) -> list[dict[str, Any]]:
    rows = conn.execute(
        f"""
        SELECT snapshot_id, ticker, market, period, fiscal_year, fiscal_quarter,
               {', '.join(FUNDAMENTAL_FIELDS)},
               source_evidence_ids_json, source_quality, freshness_status, confidence,
               missing_fields_json, field_details_json, field_missing_reasons_json, created_at, metadata_json
        FROM fundamentals_snapshot
        WHERE ticker=?
        ORDER BY id DESC
        LIMIT ?
        """,
        (ticker.upper(), max(1, int(limit or 30))),
    ).fetchall()
    return [_decode_row(row) for row in rows]


def diagnostics_from_snapshot(snapshot: dict[str, Any], ticker: str) -> dict[str, Any]:
    fields = field_quality_from_snapshot(snapshot)
    causes = root_causes_from_field_quality(fields)
    return {
        "ticker": ticker.upper(),
        "overall_data_quality_status": data_quality_status(causes),
        "fundamentals_snapshot_id": snapshot.get("snapshot_id"),
        "fundamentals_status": snapshot.get("freshness_status"),
        "root_causes": causes,
        "field_quality": fields,
    }


def select_phase12_before_snapshot(conn: sqlite3.Connection, ticker: str, after_snapshot: dict[str, Any]) -> dict[str, Any]:
    history = fundamentals_history(conn, ticker)
    if not history:
        return after_snapshot
    after_causes = set(root_cause_keys(root_causes_from_field_quality(field_quality_from_snapshot(after_snapshot))))
    best_snapshot: dict[str, Any] | None = None
    best_score = -1
    preferred_snapshot: dict[str, Any] | None = None
    for snapshot in history:
        if snapshot.get("snapshot_id") == after_snapshot.get("snapshot_id"):
            continue
        snapshot_causes = root_causes_from_field_quality(field_quality_from_snapshot(snapshot))
        causes = set(root_cause_keys(snapshot_causes))
        if not (len(causes) > len(after_causes) or bool(causes - after_causes)):
            continue
        root_codes = _code_set(snapshot_causes)
        if {"MISSING_SOURCE_EVIDENCE_ID", "AMBIGUOUS_UNIT"}.issubset(set(root_codes)):
            preferred_snapshot = preferred_snapshot or snapshot
        phase12_weight = 5 * sum(
            1 for code in root_codes if code in {"MISSING_SOURCE_EVIDENCE_ID", "AMBIGUOUS_UNIT", "FUNDAMENTALS_FIELD_CONFIDENCE_LOW"}
        )
        score = len(causes) + phase12_weight
        if score > best_score:
            best_score = score
            best_snapshot = snapshot
    return preferred_snapshot or best_snapshot or history[0]


def _code_set(causes: list[dict[str, Any]]) -> list[str]:
    return sorted({str(cause.get("code")) for cause in causes if cause.get("code")})


def _field_quality_summary(fields: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_evidence_field_count": sum(1 for detail in fields.values() if detail.get("source_evidence_id")),
        "promotion_evidence_fields": sorted(
            field for field, detail in fields.items() if detail.get("allowed_usage") == "promotion_evidence"
        ),
        "supporting_evidence_fields": sorted(
            field for field, detail in fields.items() if detail.get("allowed_usage") == "supporting_evidence"
        ),
        "context_only_fields": sorted(field for field, detail in fields.items() if detail.get("allowed_usage") == "context_only"),
        "blocked_fields": sorted(field for field, detail in fields.items() if detail.get("allowed_usage") == "blocked"),
    }


def build_phase12_data_quality_report(
    conn: sqlite3.Connection,
    ticker: str,
    *,
    refresh_fundamentals: bool = True,
) -> dict[str, Any]:
    ticker = ticker.upper()
    before_latest = latest_fundamentals_snapshot(conn, ticker)
    after_snapshot = build_fundamentals_snapshot(conn, ticker, prefer_live=True) if refresh_fundamentals or not before_latest else before_latest
    before_snapshot = select_phase12_before_snapshot(conn, ticker, after_snapshot) if before_latest else after_snapshot
    before = diagnostics_from_snapshot(before_snapshot, ticker)
    after = diagnostics_from_snapshot(after_snapshot, ticker)
    before_keys = root_cause_keys(before.get("root_causes") or [])
    after_keys = root_cause_keys(after.get("root_causes") or [])
    before_fields = before.get("field_quality") or {}
    after_fields = after.get("field_quality") or {}
    changes = field_changes(before_fields, after_fields)
    payload = {
        "generated_at": now_ts(),
        "ticker": ticker,
        "before": {
            "data_quality_status": before.get("overall_data_quality_status"),
            "root_causes": before_keys,
            "root_cause_codes": _code_set(before.get("root_causes") or []),
            "fundamentals_snapshot_id": before.get("fundamentals_snapshot_id"),
        },
        "after": {
            "data_quality_status": after.get("overall_data_quality_status"),
            "root_causes": after_keys,
            "root_cause_codes": _code_set(after.get("root_causes") or []),
            "fundamentals_snapshot_id": after.get("fundamentals_snapshot_id"),
        },
        "resolved_root_causes": sorted(set(before_keys) - set(after_keys)),
        "remaining_root_causes": after_keys,
        "resolved_root_cause_codes": sorted(set(_code_set(before.get("root_causes") or [])) - set(_code_set(after.get("root_causes") or []))),
        "field_changes": changes,
        "field_quality": _field_quality_summary(after_fields),
        "improvement_summary": {
            "missing_source_evidence_id_before": sum(1 for key in before_keys if key.startswith("MISSING_SOURCE_EVIDENCE_ID:")),
            "missing_source_evidence_id_after": sum(1 for key in after_keys if key.startswith("MISSING_SOURCE_EVIDENCE_ID:")),
            "ambiguous_unit_before": sum(1 for key in before_keys if key.startswith("AMBIGUOUS_UNIT:")),
            "ambiguous_unit_after": sum(1 for key in after_keys if key.startswith("AMBIGUOUS_UNIT:")),
            "fields_with_source_evidence_after": sum(1 for detail in after_fields.values() if detail.get("source_evidence_id")),
        },
        "before_field_quality": before_fields,
        "after_field_quality": after_fields,
    }
    register_snapshot(
        conn,
        entity_type="phase12_data_quality_before_after",
        entity_id=ticker,
        status=payload["after"]["data_quality_status"],
        source=SCRIPT_NAME,
        payload=payload,
    )
    return payload


def render_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Phase 12 Data Quality Before/After",
        "",
        f"- ticker: `{payload.get('ticker')}`",
        f"- before: `{(payload.get('before') or {}).get('data_quality_status')}`",
        f"- after: `{(payload.get('after') or {}).get('data_quality_status')}`",
        "",
        "## Resolved Root Causes",
        "",
    ]
    for cause in payload.get("resolved_root_causes") or []:
        lines.append(f"- `{cause}`")
    lines.extend(["", "## Remaining Root Causes", ""])
    for cause in payload.get("remaining_root_causes") or []:
        lines.append(f"- `{cause}`")
    lines.extend(["", "## Field Changes", "", "| Field | Before | After | Confidence | Usage |", "|---|---|---|---:|---|"])
    for field, change in (payload.get("field_changes") or {}).items():
        lines.append(
            f"| {field} | {change.get('before')} | {change.get('after')} | {change.get('after_confidence')} | {change.get('after_allowed_usage')} |"
        )
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build Phase 12 data-quality before/after report")
    parser.add_argument("--db-path", default=str(DB_PATH))
    parser.add_argument("--ticker", default="09988.HK")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--markdown", action="store_true")
    parser.add_argument("--no-refresh", action="store_true")
    args = parser.parse_args()

    conn = sqlite3.connect(args.db_path)
    conn.row_factory = sqlite3.Row
    try:
        payload = build_phase12_data_quality_report(conn, args.ticker, refresh_fundamentals=not args.no_refresh)
        conn.commit()
    finally:
        conn.close()
    if args.markdown and not args.json:
        print(render_markdown(payload))
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2, default=str))
    log_run(SCRIPT_NAME, "success", "phase12 data-quality before/after built", payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
